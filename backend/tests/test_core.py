import os
import unittest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ADMIN_EMAILS"] = "admin@cuatrovientos.org"

from app import create_app
from app.extensions import db
from app.models import Competency, CompetencyItem, Course, Enrollment, RubricLevel, User


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app({"TESTING": True, "SECRET_KEY": "a" * 48, "JWT_SECRET_KEY": "b" * 48, "JWT_COOKIE_SECURE": False, "SESSION_COOKIE_SECURE": False})
        self.app.config.update(TESTING=True)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        # Synthetic fixtures: tests never require a workbook with student responses.
        for number in range(7):
            competency = Competency(name=f"Competencia {number}", sort_order=number)
            competency.items = [CompetencyItem(statement="Prueba directa", sort_order=0),
                                CompetencyItem(statement="Prueba inversa", reverse_score=True, sort_order=1)]
            competency.rubric_levels = [RubricLevel(label=label, max_score=maximum, feedback="Orientación de prueba")
                                       for label, maximum in (("Incipiente", 2), ("En desarrollo", 3), ("Generado", 4))]
            db.session.add(competency)
        self.student = User(email="alumna@example.org", full_name="Alumna de prueba", email_verified=True)
        self.student.set_password("secret123")
        self.course = Course(name="Curso de prueba", academic_year="2026/2027")
        db.session.add_all([self.student, self.course])
        db.session.flush()
        db.session.add(Enrollment(student_id=self.student.id, course_id=self.course.id))
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def login(self, email, password):
        response = self.client.post("/api/auth/login", json={"email": email, "password": password}, headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(response.status_code, 200)
        return {"X-Requested-With": "XMLHttpRequest", "X-CSRF-TOKEN": self.client.get_cookie("csrf_access_token").value}


class QuestionnaireFlowTest(BaseTest):
    def test_questionnaire_submission_calculates_results(self):
        questionnaire = self.client.get("/api/questionnaire")
        self.assertEqual(questionnaire.status_code, 200)
        self.assertEqual(len(questionnaire.json["competencies"]), 7)

        answers = []
        for competency in Competency.query.all():
            for item in competency.items:
                answers.append({"itemId": item.id, "value": 1 if item.reverse_score else 4})
        response = self.client.post(
            "/api/student/submissions",
            headers=self.login("alumna@example.org", "secret123"),
            json={"courseId": self.course.id, "answers": answers},
        )
        self.assertEqual(response.status_code, 201)
        results = response.json["submission"]["results"]
        self.assertEqual(len(results), 7)
        self.assertTrue(all(result["level"] == "Generado" for result in results))
        self.assertTrue(all(result["score"] == 4 for result in results))

    def test_admin_role_is_read_from_environment(self):
        admin = User(email="admin@cuatrovientos.org", full_name="Administración", email_verified=True)
        admin.set_password("secret123")
        db.session.add(admin)
        db.session.commit()
        response = self.client.get("/api/admin/courses", headers=self.login(admin.email, "secret123"))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_manage_users_and_assign_tutor(self):
        admin = User(email="admin@cuatrovientos.org", full_name="Administración", email_verified=True)
        admin.set_password("secret123")
        db.session.add(admin)
        db.session.commit()
        headers = self.login(admin.email, "secret123")
        created = self.client.post("/api/admin/users", headers=headers, json={
            "email": "tutor@example.org", "fullName": "Tutor de prueba", "role": "tutor",
            "password": "secret123", "emailVerified": True,
        })
        self.assertEqual(created.status_code, 201)
        tutor_id = created.json["user"]["id"]
        assigned = self.client.post(f"/api/admin/courses/{self.course.id}/tutors", headers=headers,
                                    json={"userId": tutor_id})
        self.assertEqual(assigned.status_code, 200)
        self.assertEqual(assigned.json["course"]["tutors"][0]["id"], tutor_id)

    def test_tutor_exports_are_scoped_to_assigned_courses(self):
        tutor = User(email="tutor@example.org", full_name="Tutor", role="tutor", email_verified=True)
        tutor.set_password("secret123")
        outsider = User(email="otro@example.org", full_name="Otro tutor", role="tutor", email_verified=True)
        outsider.set_password("secret123")
        self.course.tutors.append(tutor)
        db.session.add_all([tutor, outsider])
        db.session.commit()
        allowed = self.client.get(f"/api/tutor/courses/{self.course.id}/export.xlsx",
                                  headers=self.login(tutor.email, "secret123"))
        self.assertEqual(allowed.status_code, 200)
        self.assertIn("spreadsheetml", allowed.content_type)
        forbidden = self.client.get(f"/api/tutor/courses/{self.course.id}/export.pdf",
                                    headers=self.login(outsider.email, "secret123"))
        self.assertEqual(forbidden.status_code, 403)


if __name__ == "__main__":
    unittest.main()
