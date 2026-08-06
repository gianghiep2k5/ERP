"""Application configuration loaded from environment variables / .env file."""
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


# Resolve project root: backend/app/config.py → backend/app → backend → root
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DB = _PROJECT_ROOT / "data" / "generated" / "vims_ai_demo.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # If DATABASE_URL is not set in .env, fall back to the computed path.
    DATABASE_URL: Optional[str] = None

    JWT_SECRET: str = "change-me-to-a-long-random-string-at-least-32-bytes"
    JWT_EXPIRE_MINUTES: int = 480

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"sqlite:///{_DEFAULT_DB}"


settings = Settings()
