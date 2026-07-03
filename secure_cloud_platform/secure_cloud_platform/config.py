import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")
    MASTER_KEY = os.environ.get("MASTER_KEY")  # required for file encryption

    # Default to an absolute path so SQLite works regardless of the current
    # working directory the app is launched from. Override DATABASE_URL in .env
    # with a full URL (e.g. postgresql://...) to use a different database.
    _default_sqlite_path = os.path.join(BASE_DIR, "instance", "platform.db")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{_default_sqlite_path}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_UPLOAD_MB", 25)) * 1024 * 1024

    # Session / cookie hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Set to True when serving over HTTPS in production
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") == "production"
