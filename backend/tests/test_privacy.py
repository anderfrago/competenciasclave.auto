from datetime import datetime, timedelta
from unittest.mock import patch

from app import create_app
from app.extensions import db
from app.models import Answer, Competency, CompetencyResult, Course, Enrollment, Submission, User
from test_core import BaseTest


class PrivacyTest(BaseTest):
    def test_cookie_auth_csrf_and_logout_revocation(self):
        headers = self.login(self.student.email, "secret123")
        cookie = self.client.get_cookie("access_token_cookie", path="/api/")
        self.assertTrue(cookie.http_only)
        self.assertEqual(cookie.same_site, "Lax")
        self.assertEqual(self.client.post("/api/auth/logout", headers={"X-Requested-With": "XMLHttpRequest"}).status_code, 401)
        self.assertEqual(self.client.post("/api/auth/logout", headers=headers).status_code, 200)
        self.client.set_cookie("access_token_cookie", cookie.value, path="/api/")
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_deactivated_and_changed_accounts_revoke_sessions(self):
        self.login(self.student.email, "secret123")
        self.student.active = False
        db.session.commit()
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        self.student.active = True
        self.student.auth_version += 1
        db.session.commit()
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_no_bearer_auth_or_access_token_in_response(self):
        response = self.client.post("/api/auth/login", json={"email": self.student.email, "password": "secret123"}, headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertNotIn("accessToken", response.json)
        cookie = self.client.get_cookie("access_token_cookie", path="/api/")
        fresh = self.app.test_client()
        self.assertEqual(fresh.get("/api/auth/me", headers={"Authorization": f"Bearer {cookie.value}"}).status_code, 401)

    def test_cross_origin_login_rejected(self):
        response = self.client.post("/api/auth/login", json={}, headers={"X-Requested-With": "XMLHttpRequest", "Origin": "https://external.invalid"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post("/api/auth/login", json={}).status_code, 403)

    def test_registration_requires_authorization_and_mail_delivery(self):
        data = {"email": "new@example.org", "fullName": "Nueva", "password": "long-password"}
        headers = {"X-Requested-With": "XMLHttpRequest"}
        self.assertEqual(self.client.post("/api/auth/register", json=data, headers=headers).status_code, 403)
        self.app.config["REGISTRATION_EMAILS"] = {data["email"]}
        with patch("app.routes.auth.send_email", return_value=False):
            response = self.client.post("/api/auth/register", json=data, headers=headers)
        self.assertEqual(response.status_code, 503)
        self.assertNotIn("verificationUrl", response.json)
        self.assertIsNone(User.query.filter_by(email=data["email"]).first())

    def test_verification_is_single_use(self):
        self.app.config["REGISTRATION_EMAILS"] = {"new@example.org"}
        with patch("app.routes.auth.send_email", return_value=True) as mail:
            response = self.client.post("/api/auth/register", json={"email": "new@example.org", "fullName": "Nueva", "password": "long-password"}, headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(response.status_code, 201)
        path = mail.call_args.args[2].split("/api/auth/verify/")[1]
        self.assertEqual(self.client.get(f"/api/auth/verify/{path}").status_code, 302)
        self.assertEqual(self.client.get(f"/api/auth/verify/{path}").status_code, 400)

    def test_smtp_does_not_log_personal_data(self):
        from app.services import send_email
        self.app.config["SMTP_HOST"] = ""
        with self.assertLogs(self.app.logger, level="WARNING") as logs:
            self.assertFalse(send_email("private@example.org", "subject", "secret-verification-token"))
        self.assertNotIn("private@example.org", str(logs.output))
        self.assertNotIn("secret-verification-token", str(logs.output))

    def test_closed_course_and_public_invitation_minimization(self):
        invitation = self.client.get(f"/api/invitations/{self.course.invite_code}")
        self.assertEqual(set(invitation.json["course"]), {"id", "name", "academicYear"})
        headers = self.login(self.student.email, "secret123")
        self.course.active = False
        db.session.commit()
        self.assertEqual(self.client.post("/api/student/submissions", json={"courseId": self.course.id}, headers=headers).status_code, 403)

    def test_privacy_is_public_escaped_and_responses_not_cached(self):
        self.app.config["PRIVACY_CONTROLLER"] = "<script>bad()</script>"
        response = self.client.get("/privacidad")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"&lt;script&gt;", response.data)
        self.assertEqual(response.headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(self.client.get("/api/questionnaire").headers["Cache-Control"], "no-store")

    def test_retention_requires_configuration_and_explicit_selection(self):
        runner = self.app.test_cli_runner()
        self.app.config["RETENTION_DAYS"] = ""
        self.assertNotEqual(runner.invoke(args=["purge-expired"]).exit_code, 0)
        self.app.config["RETENTION_DAYS"] = "30"
        self.assertNotEqual(runner.invoke(args=["purge-expired", "--execute"]).exit_code, 0)
        self.assertNotEqual(runner.invoke(args=["purge-expired", "--execute", "--course-id", str(self.course.id)]).exit_code, 0)
        self.assertIsNotNone(db.session.get(Course, self.course.id))

    def test_retention_preview_cascade_and_recent_activity(self):
        old = datetime.utcnow() - timedelta(days=60)
        self.course.active = False
        self.course.created_at = old
        self.course.updated_at = old
        for enrollment in self.course.enrollments:
            enrollment.updated_at = old
        submission = Submission(student=self.student, course=self.course, completed_at=old, created_at=old, updated_at=old)
        db.session.add(submission)
        db.session.flush()
        competency = Competency.query.first()
        db.session.add(Answer(submission_id=submission.id, item_id=competency.items[0].id, value=3))
        db.session.add(CompetencyResult(submission_id=submission.id, competency_id=competency.id, score=3, level="En desarrollo", feedback="Prueba"))
        db.session.commit()
        self.app.config["RETENTION_DAYS"] = "30"
        runner = self.app.test_cli_runner()
        self.assertEqual(runner.invoke(args=["purge-expired"]).exit_code, 0)
        self.assertEqual(Submission.query.count(), 1)
        submission.updated_at = datetime.utcnow()
        db.session.commit()
        args = ["purge-expired", "--execute", "--course-id", str(self.course.id)]
        self.assertNotEqual(runner.invoke(args=args).exit_code, 0)
        submission.updated_at = old
        db.session.commit()
        result = runner.invoke(args=args)
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(Course.query.count(), 0)
        for model in (Submission, Answer, CompetencyResult, Enrollment):
            self.assertEqual(model.query.count(), 0)
        self.assertEqual(User.query.count(), 1)

    def test_insecure_secrets_fail_startup(self):
        with self.assertRaises(RuntimeError):
            create_app({"SECRET_KEY": "cambia-esta-clave"})

    def test_google_never_puts_tokens_in_urls_and_blocks_conflicts(self):
        with patch("app.routes.auth.oauth") as oauth:
            oauth.google.authorize_access_token.return_value = {"userinfo": {
                "sub": "google-123", "email": self.student.email, "email_verified": True,
            }}
            response = self.client.get("/api/auth/google/callback")
            self.assertEqual(response.status_code, 302)
            self.assertNotIn("token=", response.location)
            self.assertTrue(self.client.get_cookie("access_token_cookie", path="/api/").http_only)
            oauth.google.authorize_access_token.return_value["userinfo"]["sub"] = "different-subject"
            self.assertEqual(self.client.get("/api/auth/google/callback").status_code, 403)

    def test_google_unknown_account_requires_authorization(self):
        with patch("app.routes.auth.oauth") as oauth:
            oauth.google.authorize_access_token.return_value = {"userinfo": {
                "sub": "google-unknown", "email": "unknown@example.org", "email_verified": True,
            }}
            self.assertEqual(self.client.get("/api/auth/google/callback").status_code, 403)
        self.assertEqual(User.query.count(), 1)

    def test_admin_edit_revokes_existing_session(self):
        headers = self.login(self.student.email, "secret123")
        cookie = self.client.get_cookie("access_token_cookie", path="/api/").value
        admin = User(email="admin@cuatrovientos.org", full_name="Admin", email_verified=True)
        admin.set_password("secret123")
        db.session.add(admin)
        db.session.commit()
        headers = self.login(admin.email, "secret123")
        response = self.client.patch(f"/api/admin/users/{self.student.id}", headers=headers, json={"active": False})
        self.assertEqual(response.status_code, 200)
        fresh = self.app.test_client()
        fresh.set_cookie("access_token_cookie", cookie, path="/api/")
        self.assertEqual(fresh.get("/api/auth/me").status_code, 401)

    def test_google_clears_password_created_before_email_verification(self):
        self.student.email_verified = False
        db.session.commit()
        with patch("app.routes.auth.oauth") as oauth:
            oauth.google.authorize_access_token.return_value = {"userinfo": {
                "sub": "verified-owner", "email": self.student.email, "email_verified": True,
            }}
            self.assertEqual(self.client.get("/api/auth/google/callback").status_code, 302)
        self.assertIsNone(self.student.password_hash)
        self.assertTrue(self.student.email_verified)

    def test_email_change_does_not_inherit_verification(self):
        admin = User(email="admin@cuatrovientos.org", full_name="Admin", email_verified=True)
        admin.set_password("secret123")
        db.session.add(admin)
        db.session.commit()
        headers = self.login(admin.email, "secret123")
        response = self.client.patch(f"/api/admin/users/{self.student.id}", headers=headers, json={"email": "changed@example.org", "emailVerified": True})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json["user"]["emailVerified"])

    def test_login_attempts_are_limited_across_clients(self):
        from app.models import AuthAttempt
        for _ in range(10):
            response = self.app.test_client().post("/api/auth/login", json={"email": "unknown@example.org", "password": "wrong"}, headers={"X-Requested-With": "XMLHttpRequest"})
            self.assertEqual(response.status_code, 401)
        response = self.client.post("/api/auth/login", json={"email": "unknown@example.org", "password": "wrong"}, headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response.headers)
        self.assertTrue(all(len(bucket.key) == 64 and "@" not in bucket.key for bucket in AuthAttempt.query.all()))
