"""
Job Matching API endpoint.
POST /api/v1/match — Match candidate against a job description
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security_auth import get_current_user
from app.models.user import User
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.models.job import Job
from app.models.match_result import MatchResult
from app.agents.orchestrator import AgentOrchestrator
from app.api.v1.schemas import MatchRequest, MatchResponse, MatchListResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/match", tags=["Job Matching"])

_orchestrator = None


def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


@router.post(
    "",
    response_model=MatchListResponse,
    summary="Match job against all candidates",
    description="Perform semantic matching between a job description and all candidates."
)
async def match_all_candidates(
    request: MatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Match all candidates against a job description."""
    orchestrator = get_orchestrator()
    job_dict = request.job_description.model_dump()
    
    # Save or find job
    job = Job(
        title=request.job_description.title,
        company=request.job_description.company,
        description=request.job_description.description[:5000],
        required_skills=request.job_description.required_skills,
        optional_skills=request.job_description.optional_skills,
        experience_min=request.job_description.experience_min,
        experience_max=request.job_description.experience_max,
    )
    db.add(job)
    db.flush()

    candidates = db.query(Candidate).all()
    results = []
    
    for candidate in candidates:
        resume = db.query(Resume).filter(Resume.candidate_id == candidate.id).order_by(Resume.created_at.desc()).first()
        if not resume or not resume.parsed_data:
            continue
            
        parsed = resume.parsed_data
        from app.agents.skill_normalizer import SkillNormalizerAgent
        normalizer = SkillNormalizerAgent()
        normalized = normalizer.normalize(parsed.get("skills", []), parsed.get("experience", []))
        
        candidate_profile = {
            "name": candidate.name,
            "email": candidate.email,
            "summary": parsed.get("summary", ""),
            "skills": normalized,
            "experience": parsed.get("experience", []),
            "education": parsed.get("education", []),
        }
        
        match_result = orchestrator.match_candidate(candidate_profile, job_dict)
        if match_result.get("status") == "failed":
            continue
            
        overall_score = match_result.get("overall_score", 0)
        
        # Only include candidates above threshold (e.g., 50%)
        if overall_score >= 50.0:
            match_record = MatchResult(
                candidate_id=candidate.id,
                job_id=job.id,
                overall_score=overall_score,
                skill_score=match_result.get("skill_score", 0),
                experience_score=match_result.get("experience_score", 0),
                semantic_score=match_result.get("semantic_score", 0),
                matching_skills=match_result.get("matching_skills", []),
                missing_skills=match_result.get("missing_skills", []),
                optional_missing=match_result.get("optional_missing", []),
                explanation=match_result.get("explanation", ""),
                recommendations=match_result.get("recommendations", []),
            )
            db.add(match_record)
            
            # Use raw skills for simple display
            raw_skills = parsed.get("skills", [])
            
            results.append(MatchResponse(
                candidate_id=candidate.id,
                name=candidate.name or "Unknown",
                email=candidate.email or "Unknown",
                skills=raw_skills,
                resume_id=resume.id,
                status="success",
                overall_score=overall_score,
                skill_score=match_result.get("skill_score", 0),
                experience_score=match_result.get("experience_score", 0),
                semantic_score=match_result.get("semantic_score", 0),
                matching_skills=match_result.get("matching_skills", []),
                missing_skills=match_result.get("missing_skills", []),
                optional_missing=match_result.get("optional_missing", []),
                explanation=match_result.get("explanation", ""),
                recommendations=match_result.get("recommendations", []),
                match_time_ms=match_result.get("match_time_ms", 0),
            ))

    db.commit()
    
    # Sort by overall score descending
    results.sort(key=lambda x: x.overall_score, reverse=True)
    
    return MatchListResponse(
        matches=results,
        total_evaluated=len(candidates)
    )

async def match_candidate_job(
    request: MatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Match a candidate against a job description."""

    orchestrator = get_orchestrator()
    candidate_profile = None

    # ── Option A: Use existing candidate from database ───────────────────
    if request.candidate_id:
        candidate = db.query(Candidate).filter(Candidate.id == request.candidate_id).first()
        if not candidate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate with ID {request.candidate_id} not found",
            )

        # Get latest parsed resume data
        resume = (
            db.query(Resume)
            .filter(Resume.candidate_id == request.candidate_id)
            .order_by(Resume.created_at.desc())
            .first()
        )

        if not resume or not resume.parsed_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No parsed resume data found for this candidate",
            )

        parsed = resume.parsed_data
        # Re-normalize skills
        from app.agents.skill_normalizer import SkillNormalizerAgent
        normalizer = SkillNormalizerAgent()
        normalized = normalizer.normalize(parsed.get("skills", []), parsed.get("experience", []))

        candidate_profile = {
            "name": candidate.name,
            "email": candidate.email,
            "summary": parsed.get("summary", ""),
            "skills": normalized,
            "experience": parsed.get("experience", []),
            "education": parsed.get("education", []),
        }

    # ── Option B: Use provided candidate profile ────────────────────────
    elif request.candidate_profile:
        candidate_profile = request.candidate_profile
        # Ensure skills are in the right format
        skills = candidate_profile.get("skills", [])
        if isinstance(skills, list):
            from app.agents.skill_normalizer import SkillNormalizerAgent
            normalizer = SkillNormalizerAgent()
            normalized = normalizer.normalize(skills)
            candidate_profile["skills"] = normalized

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either candidate_id or candidate_profile",
        )

    # ── Run matching ─────────────────────────────────────────────────────
    job_dict = request.job_description.model_dump()
    match_result = orchestrator.match_candidate(candidate_profile, job_dict)

    if match_result.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Matching failed: {match_result.get('error', 'Unknown error')}",
        )

    # ── Save job and match result to database ────────────────────────────
    try:
        # Save or find job
        job = Job(
            title=request.job_description.title,
            company=request.job_description.company,
            description=request.job_description.description[:5000],
            required_skills=request.job_description.required_skills,
            optional_skills=request.job_description.optional_skills,
            experience_min=request.job_description.experience_min,
            experience_max=request.job_description.experience_max,
        )
        db.add(job)
        db.flush()

        if request.candidate_id:
            match_record = MatchResult(
                candidate_id=request.candidate_id,
                job_id=job.id,
                overall_score=match_result.get("overall_score", 0),
                skill_score=match_result.get("skill_score", 0),
                experience_score=match_result.get("experience_score", 0),
                semantic_score=match_result.get("semantic_score", 0),
                matching_skills=match_result.get("matching_skills", []),
                missing_skills=match_result.get("missing_skills", []),
                optional_missing=match_result.get("optional_missing", []),
                explanation=match_result.get("explanation", ""),
                recommendations=match_result.get("recommendations", []),
            )
            db.add(match_record)

        db.commit()
    except Exception as e:
        logger.error(f"Failed to save match result: {e}")
        db.rollback()

    return MatchResponse(
        status="success",
        overall_score=match_result.get("overall_score", 0),
        skill_score=match_result.get("skill_score", 0),
        experience_score=match_result.get("experience_score", 0),
        semantic_score=match_result.get("semantic_score", 0),
        matching_skills=match_result.get("matching_skills", []),
        missing_skills=match_result.get("missing_skills", []),
        optional_missing=match_result.get("optional_missing", []),
        explanation=match_result.get("explanation", ""),
        recommendations=match_result.get("recommendations", []),
        match_time_ms=match_result.get("match_time_ms", 0),
    )
