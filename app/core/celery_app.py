"""
Celery application setup for async task processing.
Falls back to synchronous execution if Redis is not available.
"""

import logging

logger = logging.getLogger(__name__)

try:
    from celery import Celery
    from app.core.config import get_settings

    settings = get_settings()

    celery_app = Celery(
        "resumatch",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
        include=["app.tasks.resume_tasks"],
    )

    # ── Celery Configuration ─────────────────────────────────────────────
    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,            # Re-deliver tasks if worker crashes
        worker_prefetch_multiplier=1,   # Fair task distribution
        result_expires=3600,            # Results expire after 1 hour
        task_soft_time_limit=300,       # 5 min soft limit
        task_time_limit=600,            # 10 min hard limit
    )

    CELERY_AVAILABLE = True
    logger.info("Celery initialized with Redis broker")

except Exception as e:
    celery_app = None
    CELERY_AVAILABLE = False
    logger.warning(f"Celery not available ({e}). Tasks will run synchronously.")
