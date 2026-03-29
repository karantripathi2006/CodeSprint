"""
Celery tasks for async resume processing.
Falls back to synchronous execution when Celery/Redis is unavailable.
"""

import logging
import json
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

try:
    from app.core.celery_app import celery_app, CELERY_AVAILABLE
except ImportError:
    celery_app = None
    CELERY_AVAILABLE = False


def _get_orchestrator():
    """Get orchestrator instance (created per-task to avoid serialization issues)."""
    from app.agents.orchestrator import AgentOrchestrator
    return AgentOrchestrator()


# ── Task Definitions ─────────────────────────────────────────────────────────

if CELERY_AVAILABLE and celery_app:
    @celery_app.task(bind=True, name="process_resume", max_retries=2)
    def process_resume_task(self, file_content_b64: str, filename: str) -> Dict[str, Any]:
        """
        Celery task: Process a single resume asynchronously.
        File content is passed as base64 to support JSON serialization.
        """
        import base64
        try:
            content = base64.b64decode(file_content_b64)
            orchestrator = _get_orchestrator()
            result = orchestrator.process_resume(content, filename)
            # Remove raw_text from result to reduce storage
            if result.get("parsed_data"):
                result["parsed_data"].pop("raw_text", None)
            return result
        except Exception as e:
            logger.error(f"Task failed for {filename}: {e}")
            raise self.retry(exc=e, countdown=5)

    @celery_app.task(bind=True, name="batch_process", max_retries=1)
    def batch_process_task(self, files_data: List[Dict]) -> Dict[str, Any]:
        """
        Celery task: Process multiple resumes in batch.
        files_data: List of {"filename": str, "content_b64": str}
        """
        import base64
        try:
            orchestrator = _get_orchestrator()
            files = []
            for f in files_data:
                files.append({
                    "filename": f["filename"],
                    "content": base64.b64decode(f["content_b64"]),
                })
            return orchestrator.process_batch(files)
        except Exception as e:
            logger.error(f"Batch task failed: {e}")
            raise self.retry(exc=e, countdown=10)

else:
    # ── Fallback: Synchronous Execution ──────────────────────────────────
    def process_resume_task(file_content: bytes, filename: str) -> Dict[str, Any]:
        """Synchronous fallback for single resume processing."""
        orchestrator = _get_orchestrator()
        result = orchestrator.process_resume(file_content, filename)
        return result

    def batch_process_task(files: List[Dict]) -> Dict[str, Any]:
        """Synchronous fallback for batch processing."""
        orchestrator = _get_orchestrator()
        return orchestrator.process_batch(files)
