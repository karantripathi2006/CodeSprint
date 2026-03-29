"""
Resume Parsing API endpoints.
POST /api/v1/parse      — Upload and process a single resume
POST /api/v1/parse/batch — Upload multiple resumes for batch processing
"""

import logging
import uuid
import os
from typing import List

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security_auth import get_current_user
from app.models.user import User
from app.core.config import get_settings
import aiofiles
from app.agents.orchestrator import AgentOrchestrator
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.api.v1.schemas import ResumeProcessingResult, BatchProcessingResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/parse", tags=["Resume Parsing"])

# ── Singleton orchestrator ───────────────────────────────────────────────────
_orchestrator = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


# ═══════════════════════════════════════════════════════════════════════════════
#  POST /api/v1/parse — Single Resume Upload
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "",
    response_model=ResumeProcessingResult,
    summary="Parse a single resume",
    description="Upload a resume (PDF, DOCX, or TXT) to extract structured data and normalize skills.",
    responses={
        200: {
            "description": "Resume parsed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "candidate_id": 1,
                        "filename": "john_doe_resume.pdf",
                        "parsed_data": {
                            "name": "John Doe",
                            "email": "john@example.com",
                            "skills": ["Python", "FastAPI", "PostgreSQL"],
                        },
                        "normalized_skills": {
                            "normalized_skills": ["Python", "FastAPI", "PostgreSQL"],
                            "inferred_skills": ["Web Frameworks"],
                            "proficiency_map": {"Python": 0.8},
                        },
                    }
                }
            },
        },
        400: {"description": "Invalid file format"},
    },
)
async def parse_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Parse a single resume and return structured data."""

    # Validate file type
    allowed_extensions = {"pdf", "docx", "txt", "doc"}
    filename = file.filename or "unknown.txt"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: .{ext}. Allowed: {', '.join(allowed_extensions)}",
        )

    # Read file content
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file uploaded",
        )

    # Validate file size (max 10MB)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10MB.",
        )

    # Save file to disk
    settings = get_settings()
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    async with aiofiles.open(file_path, 'wb') as out_file:
        await out_file.write(content)

    # Process through orchestrator
    orchestrator = get_orchestrator()
    result = orchestrator.process_resume(content, filename)


    # Save to database
    candidate_id = None
    try:
        parsed = result.get("parsed_data", {})
        candidate = Candidate(
            name=parsed.get("name", ""),
            email=parsed.get("email", ""),
            phone=parsed.get("phone", ""),
            location=parsed.get("location", ""),
            summary=parsed.get("summary", ""),
            raw_resume_text=parsed.get("raw_text", "")[:10000],  # Limit stored text
        )
        # db.add(candidate)
        # db.flush()

        # resume_record = Resume(
        #     candidate_id=candidate.id,
        #     filename=unique_filename,
        #     file_type=ext,
        #     file_size=len(content),
        #     parsed_data=parsed,
        #     status=result.get("status", "completed"),
        #     processing_time_ms=result.get("metadata", {}).get("total_time_ms", 0),
        # )
        # db.add(resume_record)
        # db.commit()
        # candidate_id = candidate.id
        candidate_id = None # Do not save to database during parsing
        logger.info(f"Parsed candidate {parsed.get('name', 'Unknown')} (Not saved to DB per request)")
    except Exception as e:
        logger.error(f"Error formulating parsed data: {e}")
        # db.rollback()

    return ResumeProcessingResult(
        status=result.get("status", "success"),
        candidate_id=candidate_id,
        filename=unique_filename,
        parsed_data=result.get("parsed_data"),
        normalized_skills=result.get("normalized_skills"),
        errors=result.get("errors", []),
        metadata=result.get("metadata", {}),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  POST /api/v1/parse/batch — Batch Resume Processing
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/batch",
    response_model=BatchProcessingResult,
    summary="Batch process multiple resumes",
    description="Upload multiple resumes for batch processing. Returns results for all files.",
)
async def parse_batch(
    files: List[UploadFile] = File(..., description="Multiple resume files"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process multiple resumes in batch."""

    if len(files) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 files per batch. Please split into smaller batches.",
        )

    # Read all files
    file_data = []
    settings = get_settings()
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    unique_filenames_map = {}
    
    for f in files:
        content = await f.read()
        if content:
            original_name = f.filename or f"resume_{len(file_data)}.txt"
            unique_filename = f"{uuid.uuid4()}_{original_name}"
            file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
            
            async with aiofiles.open(file_path, 'wb') as out_file:
                await out_file.write(content)
                
            unique_filenames_map[original_name] = unique_filename
            
            file_data.append({
                "filename": original_name,
                "content": content,
            })

    if not file_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid files uploaded.",
        )

    # Process batch
    orchestrator = get_orchestrator()
    batch_result = orchestrator.process_batch(file_data)

    # Save results to database
    results = []
    for item in batch_result.get("results", []):
        candidate_id = None
        try:
            parsed = item.get("parsed_data", {}) or {}
            candidate = Candidate(
                name=parsed.get("name", ""),
                email=parsed.get("email", ""),
                phone=parsed.get("phone", ""),
                location=parsed.get("location", ""),
                raw_resume_text=parsed.get("raw_text", "")[:10000],
            )
            # db.add(candidate)
            # db.flush()
            # candidate_id = candidate.id
            candidate_id = None
        except Exception:
            # db.rollback()
            pass

        results.append(ResumeProcessingResult(
            status=item.get("status", "success"),
            candidate_id=candidate_id,
            filename=unique_filenames_map.get(item.get("filename", ""), item.get("filename", "")),
            parsed_data=item.get("parsed_data"),
            normalized_skills=item.get("normalized_skills"),
            errors=item.get("errors", []),
            metadata=item.get("metadata", {}),
        ))

    # try:
    #     db.commit()
    # except Exception:
    #     db.rollback()

    task_id = str(uuid.uuid4())
    return BatchProcessingResult(
        task_id=task_id,
        status="completed",
        total=batch_result.get("total", len(files)),
        successful=batch_result.get("successful", 0),
        failed=batch_result.get("failed", 0),
        total_time_ms=batch_result.get("total_time_ms", 0),
        results=results,
    )
