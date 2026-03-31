"""
Jobs API endpoints.
POST /api/v1/jobs     — Save a job description
GET  /api/v1/jobs     — List all saved jobs
GET  /api/v1/jobs/{id} — Get a specific job
DELETE /api/v1/jobs/{id} — Delete a job
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security_auth import get_current_user
from app.models.user import User
from app.models.job import Job
from app.api.v1.schemas import JobDescriptionInput, JobResponse, JobListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post(
    "",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a job description",
    description="Persist a job description so it can be referenced by ID in future match requests.",
)
def create_job(
    job_input: JobDescriptionInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = Job(
        title=job_input.title,
        company=job_input.company,
        description=job_input.description[:5000],
        required_skills=job_input.required_skills,
        optional_skills=job_input.optional_skills,
        experience_min=job_input.experience_min,
        experience_max=job_input.experience_max,
        location=job_input.location,
        job_type=job_input.job_type,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info(f"Saved job: '{job.title}' at '{job.company}' (id={job.id})")
    return job


@router.get(
    "",
    response_model=JobListResponse,
    summary="List all saved jobs",
)
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    return JobListResponse(jobs=jobs, total=len(jobs))


@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get a job by ID",
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job",
)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    db.delete(job)
    db.commit()
    return None
