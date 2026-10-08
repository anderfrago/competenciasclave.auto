import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

class Config:
    @staticmethod
    def values():
        return _values()

def _values():
    class Environment:
        SECRET_KEY = os.getenv("SECRET_KEY", "")
        JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200").rstrip("/")
        BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000").rstrip("/")
        SPA_DIST_PATH = os.getenv("SPA_DIST_PATH", "").strip()
        ADMIN_EMAILS = {
            email.strip().lower()
            for email in os.getenv(
                "ADMIN_EMAILS", ""
            ).split(",")
            if email.strip()
        }
        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
        SMTP_HOST = os.getenv("SMTP_HOST")
        SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
        SMTP_USERNAME = os.getenv("SMTP_USERNAME")
        SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
        SMTP_FROM = os.getenv("SMTP_FROM", "no-reply@example.com")

    Environment.SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    Environment.JWT_TOKEN_LOCATION = ["cookies"]
    Environment.JWT_COOKIE_CSRF_PROTECT = True
    Environment.JWT_COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"
    Environment.JWT_COOKIE_SAMESITE = "Lax"
    Environment.JWT_ACCESS_COOKIE_PATH = "/api/"
    Environment.JWT_ACCESS_TOKEN_EXPIRES = 7200
    Environment.SESSION_COOKIE_SECURE = Environment.JWT_COOKIE_SECURE
    Environment.SESSION_COOKIE_HTTPONLY = True
    Environment.SESSION_COOKIE_SAMESITE = "Lax"
    Environment.MAX_CONTENT_LENGTH = 1024 * 1024
    Environment.REGISTRATION_EMAILS = {email.strip().lower() for email in os.getenv("REGISTRATION_EMAILS", "").split(",") if email.strip()}
    for key in ("RETENTION_DAYS", "PRIVACY_CONTROLLER", "PRIVACY_CONTACT", "PRIVACY_LEGAL_BASIS", "PRIVACY_RETENTION", "PRIVACY_PROVIDERS"):
        setattr(Environment, key, os.getenv(key, ""))
    return {key: getattr(Environment, key) for key in vars(Environment) if key.isupper()}
