import os
from pathlib import Path


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "desarrollo-cambiar-por-una-clave-de-al-menos-32-caracteres")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4200").rstrip("/")
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:5000").rstrip("/")
    SPA_DIST_PATH = os.getenv("SPA_DIST_PATH", "").strip()
    ADMIN_EMAILS = {
        email.strip().lower()
        for email in os.getenv(
            "ADMIN_EMAILS", "ander_frago@cuatrovientos.org,fernando_olcoz@cuatrovientos.org"
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

    @staticmethod
    def database_uri(instance_path: str) -> str:
        configured = os.getenv("DATABASE_URL")
        if configured:
            return configured
        return f"sqlite:///{Path(instance_path) / 'autopercepcion.db'}"
