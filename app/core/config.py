"""
Application configuration loaded from environment variables.
Uses pydantic-settings for type-safe configuration management.
"""

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load local env values early so compatibility validators can inspect
# alternate variable names as plain environment variables.
load_dotenv()


class Settings(BaseSettings):
    """Central configuration for the ResuMatch AI application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "ResuMatch AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # ── Security ─────────────────────────────────────────────────────────
    API_KEY: str = "dev-api-key-change-in-production"

    # ── Database ─────────────────────────────────────────────────────────
    # Falls back to SQLite if PostgreSQL is not available
    DATABASE_URL: str = "sqlite:///./resumatch.db"

    # ── Redis ────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── ChromaDB ─────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # ── ML Models ────────────────────────────────────────────────────────
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── LLM / Communication Agent ───────────────────────────────────────
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_TIMEOUT_S: int = 20

    # ── Matching Weights (must sum to 1.0) ───────────────────────────────
    SKILL_WEIGHT: float = 0.50
    EXPERIENCE_WEIGHT: float = 0.30
    EDUCATION_WEIGHT: float = 0.20

    # ── Rate Limiting ────────────────────────────────────────────────────
    RATE_LIMIT: str = "30/minute"

    # ── File Upload ──────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "./uploads"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        """Accept common deployment strings like 'release' or 'dev'."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
                return True
            if normalized in {"0", "false", "no", "off", "release", "production", "prod"}:
                return False
        return value

    @field_validator("GROQ_API_KEY", mode="before")
    @classmethod
    def resolve_groq_key(cls, value):
        """Prefer GROQ_API_KEY, but allow legacy local env names as fallback."""
        if isinstance(value, str) and value.strip():
            return value.strip()

        return (
            os.getenv("GROQ_API_KEY", "").strip()
            or os.getenv("GROQ_API_KEY1KD", "").strip()
            or os.getenv("GROQ_API_KEY2AS", "").strip()
        )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    return Settings()
