"""
Task Status API endpoint.
GET /api/v1/tasks/{task_id} — Poll async Celery task status (or return completed for sync fallback)
"""

import logging
from fastapi import APIRouter, Depends

from app.core.security_auth import get_current_user
from app.models.user import User
from app.api.v1.schemas import TaskStatusResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get async task status",
    description="Poll the status of a batch processing task. Returns 'success' when done.",
)
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        from app.core.celery_app import celery_app, CELERY_AVAILABLE
        if CELERY_AVAILABLE:
            from celery.result import AsyncResult
            result = AsyncResult(task_id, app=celery_app)
            celery_status_map = {
                "PENDING": "pending",
                "STARTED": "started",
                "SUCCESS": "success",
                "FAILURE": "failure",
                "RETRY": "started",
                "REVOKED": "failure",
            }
            mapped = celery_status_map.get(result.status, "unknown")
            error = str(result.result) if mapped == "failure" else None
            data = result.result if mapped == "success" else None
            return TaskStatusResponse(task_id=task_id, status=mapped, result=data, error=error)
    except Exception as e:
        logger.warning(f"Celery task lookup failed: {e}")

    # Fallback: sync mode — batch tasks complete immediately, so any stored task_id is done
    return TaskStatusResponse(task_id=task_id, status="success")
