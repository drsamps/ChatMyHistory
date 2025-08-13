import os
from dataclasses import dataclass


@dataclass
class Config:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key")

    # SQLAlchemy / MySQL
    _RAW_URI: str | None = os.getenv("SQLALCHEMY_DATABASE_URI")
    if _RAW_URI and "${" not in _RAW_URI:
        SQLALCHEMY_DATABASE_URI: str = os.path.expandvars(_RAW_URI)
    else:
        _mysql_user = os.getenv("MYSQL_USER")
        _mysql_password = os.getenv("MYSQL_PASSWORD", "")
        _mysql_host = os.getenv("MYSQL_HOST", "localhost")
        _mysql_port = os.getenv("MYSQL_PORT", "3306")
        _mysql_db = os.getenv("MYSQL_DB")
        if not _mysql_user or not _mysql_db:
            raise RuntimeError(
                "Database configuration missing. Set SQLALCHEMY_DATABASE_URI or MYSQL_USER and MYSQL_DB in .env."
            )
        SQLALCHEMY_DATABASE_URI: str = (
            f"mysql+pymysql://{_mysql_user}:{_mysql_password}@{_mysql_host}:{_mysql_port}/{_mysql_db}"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS: bool = (
        os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS", "false").lower() == "true"
    )

    # Storage
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "storage/uploads")
    MEDIA_DIR: str = os.getenv("MEDIA_DIR", "storage/media")

    # LLM
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai").lower()
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: str | None = os.getenv("GOOGLE_API_KEY")

    # Transcription
    TRANSCRIPTION_PROVIDER: str = os.getenv("TRANSCRIPTION_PROVIDER", "openai").lower()
