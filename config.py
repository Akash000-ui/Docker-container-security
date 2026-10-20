"""Application configuration.

Environment-specific values are kept outside the application package so the
same code can be used for development, testing, and deployment.
"""

import os
from pathlib import Path


class Config:
    """Base configuration for the local academic prototype."""

    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def database_uri(instance_path: str) -> str:
        """Return the configured database URL or the local SQLite database."""

        configured_uri = os.getenv("DATABASE_URL")
        if configured_uri:
            return configured_uri

        database_path = Path(instance_path) / "security_monitor.db"
        return f"sqlite:///{database_path.as_posix()}"

