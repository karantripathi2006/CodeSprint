"""
ResuMatch AI — FastAPI Application Entry Point
================================================
Multi-Agent AI System for Intelligent Resume Parsing,
Skill Normalization, and Semantic Job Matching.

Run with: uvicorn app.main:app --reload
Docs at:  http://localhost:8000/docs
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.database import init_db

# ── Logging Setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
settings = get_settings()

# ── Rate Limiter ─────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ── Lifecycle Events ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize database tables
    init_db()
    logger.info("✅ Database initialized")

    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Seed skill taxonomy if needed
    try:
        from app.agents.skill_normalizer import SkillNormalizerAgent
        normalizer = SkillNormalizerAgent()
        logger.info(f"✅ Skill taxonomy loaded ({len(normalizer.all_known_skills)} skills)")
    except Exception as e:
        logger.warning(f"⚠️ Skill taxonomy loading: {e}")

    yield  # ← App is running

    logger.info("🛑 Shutting down ResuMatch AI")


# ── App Initialization ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "🧠 **Multi-Agent AI System** for intelligent resume parsing, "
        "skill normalization, and semantic job matching.\n\n"
        "### Agents\n"
        "1. **Resume Parser** — Extracts structured data from PDF, DOCX, TXT resumes\n"
        "2. **Skill Normalizer** — Maps skills to taxonomy, resolves synonyms, estimates proficiency\n"
        "3. **Semantic Matcher** — Computes match scores using embeddings and weighted scoring\n\n"
        "### Authentication\n"
        "All endpoints require an `X-API-Key` header (debug mode allows unauthenticated access)."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ───────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register API Routes ─────────────────────────────────────────────────────
from app.api.v1.parse import router as parse_router
from app.api.v1.candidates import router as candidates_router
from app.api.v1.match import router as match_router
from app.api.v1.skills import router as skills_router
from app.api.v1.auth import router as auth_router
from app.api.v1.resume import router as resume_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(resume_router, prefix="/api/v1")
app.include_router(parse_router, prefix="/api/v1")
app.include_router(candidates_router, prefix="/api/v1")
app.include_router(match_router, prefix="/api/v1")
app.include_router(skills_router, prefix="/api/v1")

# ── Serve Frontend Static Files ─────────────────────────────────────────────
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.isdir(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")


# ── Root & Health Endpoints ──────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
        "frontend": "/frontend/index.html",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    health = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "database": "unknown",
        "redis": "unknown",
    }

    # Check database
    try:
        from app.core.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health["database"] = "connected"
    except Exception as e:
        health["database"] = f"error: {str(e)}"

    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL, socket_timeout=2)
        r.ping()
        health["redis"] = "connected"
    except Exception:
        health["redis"] = "unavailable (running in sync mode)"

    return health


# ── Global Error Handler ────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all error handler for unhandled exceptions."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error. Please try again or contact support.",
            "error": str(exc) if settings.DEBUG else "Internal server error",
        },
    )
