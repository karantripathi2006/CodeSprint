"""
Application configuration loaded from environment variables.
Uses pydantic-settings for type-safe configuration management.
"""

import os
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Central configuration for the ResuMatch AI application."""

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

    # ── Matching Weights (must sum to 1.0) ───────────────────────────────
    SKILL_WEIGHT: float = 0.50
    EXPERIENCE_WEIGHT: float = 0.30
    EDUCATION_WEIGHT: float = 0.20

    # ── Rate Limiting ────────────────────────────────────────────────────
    RATE_LIMIT: str = "30/minute"

    # ── File Upload ──────────────────────────────────────────────────────
    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "./uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    return Settings()
