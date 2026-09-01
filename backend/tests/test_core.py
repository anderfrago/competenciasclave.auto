import os
import unittest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ADMIN_EMAILS"] = "admin@cuatrovientos.org"

from app import create_app
from app.extensions import db
from app.models import Competency, Course, Enrollment, User
from app.seed_data import seed_database


class QuestionnaireFlowTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update(TESTING=True)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        seed_database()
        self.student = User(email="alumna@example.org", full_name="Alumna de prueba", email_verified=True)
        self.student.set_password("secret123")
        self.course = Course(name="1º Desarrollo", academic_year="2026/2027")
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
        response = self.client.post("/api/auth/login", json={"email": email, "password": password})
        self.assertEqual(response.status_code, 200)
        return {"Authorization": f"Bearer {response.json['accessToken']}"}

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
