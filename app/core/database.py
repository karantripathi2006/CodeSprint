"""
Database engine and session management.
Supports PostgreSQL (production) and SQLite (development/hackathon).
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Create Engine ────────────────────────────────────────────────────────────
# Use appropriate connection args based on database type
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}  # SQLite needs this for FastAPI
    logger.info("Using SQLite database (hackathon mode)")
else:
    logger.info("Using PostgreSQL database")

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG,
    pool_pre_ping=True,  # Verify connections before use
)

# ── Session Factory ──────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── Base Model ───────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# ── Dependency ───────────────────────────────────────────────────────────────
def get_db():
    """FastAPI dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables. Called at application startup."""
    # Import all models so they are registered with Base
    import app.models.candidate  # noqa: F401
    import app.models.resume  # noqa: F401
    import app.models.skill  # noqa: F401
    import app.models.candidate_skill  # noqa: F401
    import app.models.job  # noqa: F401
    import app.models.match_result  # noqa: F401
    import app.models.user  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
