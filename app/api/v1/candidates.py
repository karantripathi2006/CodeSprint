"""
Candidate Skills API endpoint.
GET /api/v1/candidates/{id}/skills — Get normalized skills for a candidate
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security_auth import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.api.v1.schemas import CandidateSkillResponse, CandidateListResponse, CandidateSummary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.get(
    "",
    response_model=CandidateListResponse,
    summary="List all candidates",
    description="Retrieve a list of all parsed candidates with their skills."
)
def get_all_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).all()
    results = []
    
    for c in candidates:
        # Get latest resume for this candidate
        resume = db.query(Resume).filter(Resume.candidate_id == c.id).order_by(Resume.created_at.desc()).first()
        skills = []
        if resume and resume.parsed_data:
            skills = resume.parsed_data.get("skills", [])
            
        results.append(CandidateSummary(
            id=c.id,
            name=c.name or "Unknown",
            email=c.email or "Unknown",
            skills=", ".join(skills) if skills else "No skills listed",
            resume_id=resume.id if resume else None
        ))
        
    return CandidateListResponse(candidates=results, total=len(results))

@router.delete(
    "/{candidate_id}",
    summary="Delete candidate",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    # Find active resumes for deletion from disk
    resumes = db.query(Resume).filter(Resume.candidate_id == candidate_id).all()
    settings = get_settings()
    
    for res in resumes:
        if res.filename:
            file_path = os.path.join(settings.UPLOAD_DIR, res.filename)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Failed to delete file {file_path}: {e}")
                    
    db.delete(candidate)
    db.commit()
    
    return None

@router.get(
    "/{candidate_id}/skills",
    response_model=CandidateSkillResponse,
    summary="Get candidate skills",
    description="Retrieve the normalized skills for a specific candidate by their ID.",
    responses={
        200: {
            "description": "Candidate skills retrieved",
            "content": {
                "application/json": {
                    "example": {
                        "candidate_id": 1,
                        "candidate_name": "John Doe",
                        "total_skills": 8,
                        "skills": [
                            {"name": "Python", "category": "Programming Languages", "proficiency": 0.85, "source": "resume"},
                            {"name": "FastAPI", "category": "Web Frameworks", "proficiency": 0.7, "source": "resume"},
                        ],
                    }
                }
            },
        },
        404: {"description": "Candidate not found"},
    },
)
async def get_candidate_skills(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get normalized skills for a candidate."""

    # Find candidate
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found",
        )

    # Get most recent resume's parsed data
    resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate_id)
        .order_by(Resume.created_at.desc())
        .first()
    )

    skills = []
    if resume and resume.parsed_data:
        parsed = resume.parsed_data
        raw_skills = parsed.get("skills", [])

        # Re-normalize skills for fresh response
        try:
            from app.agents.skill_normalizer import SkillNormalizerAgent
            normalizer = SkillNormalizerAgent()
            normalized = normalizer.normalize(raw_skills)

            for skill_name in normalized.get("all_skills", []):
                category = normalizer.get_category_for_skill(skill_name)
                proficiency = normalized.get("proficiency_map", {}).get(skill_name, 0.5)
                source = "inferred" if skill_name in normalized.get("inferred_skills", []) else "resume"

                skills.append({
                    "name": skill_name,
                    "category": category,
                    "proficiency": proficiency,
                    "source": source,
                    "is_normalized": skill_name in normalized.get("normalized_skills", []),
                })
        except Exception as e:
            logger.error(f"Skill normalization failed for candidate {candidate_id}: {e}")
            # Fallback: return raw skills
            for s in raw_skills:
                skills.append({
                    "name": s,
                    "category": "Unknown",
                    "proficiency": 0.5,
                    "source": "resume",
                    "is_normalized": False,
                })

    return CandidateSkillResponse(
        candidate_id=candidate_id,
        candidate_name=candidate.name or "",
        total_skills=len(skills),
        skills=skills,
    )
