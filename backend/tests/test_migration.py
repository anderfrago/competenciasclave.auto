import tempfile
import unittest
from pathlib import Path

from flask_migrate import upgrade
from sqlalchemy import text

from app import create_app
from app.extensions import db


class MigrationTest(unittest.TestCase):
    def test_upgrade_preserves_existing_account(self):
        temp_root = Path(__file__).resolve().parents[2] / ".tmp"
        temp_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as folder:
            app = create_app({
                "TESTING": True, "SECRET_KEY": "a" * 48, "JWT_SECRET_KEY": "b" * 48,
                "SQLALCHEMY_DATABASE_URI": f"sqlite:///{Path(folder) / 'migration.db'}",
            })
            with app.app_context():
                migrations = str(Path(__file__).resolve().parents[1] / "migrations")
                upgrade(directory=migrations, revision="7182b36853ab")
                db.session.execute(text("INSERT INTO users (id,email,full_name,role,email_verified,auth_provider,created_at,updated_at) VALUES (1,'existing@example.org','Existing','student',1,'local',CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)"))
                db.session.commit()
                upgrade(directory=migrations)
                row = db.session.execute(text("SELECT email, active, auth_version FROM users WHERE id=1")).one()
                self.assertEqual(tuple(row), ("existing@example.org", 1, 1))
                db.session.remove()
                db.engine.dispose()
