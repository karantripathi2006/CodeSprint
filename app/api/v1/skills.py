"""
Skill Taxonomy API endpoint.
GET /api/v1/skills/taxonomy — Returns the full skill taxonomy tree
"""

import logging
from fastapi import APIRouter, Depends

from app.core.security_auth import get_current_user
from app.models.user import User
from app.agents.skill_normalizer import SkillNormalizerAgent
from app.api.v1.schemas import SkillTaxonomyResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/skills", tags=["Skills"])

_normalizer = None


def get_normalizer():
    global _normalizer
    if _normalizer is None:
        _normalizer = SkillNormalizerAgent()
    return _normalizer


@router.get(
    "/taxonomy",
    response_model=SkillTaxonomyResponse,
    summary="Get skill taxonomy",
    description="Returns the complete hierarchical skill taxonomy with categories, "
                "skills, synonyms, and parent-child relationships.",
    responses={
        200: {
            "description": "Skill taxonomy tree",
            "content": {
                "application/json": {
                    "example": {
                        "categories": {
                            "Programming Languages": {
                                "skills": ["Python", "JavaScript", "Java"],
                                "synonyms": {"JS": "JavaScript"},
                            }
                        },
                        "total_skills": 50,
                    }
                }
            },
        }
    },
)
async def get_taxonomy(current_user: User = Depends(get_current_user)):
    """Return the full skill taxonomy."""
    normalizer = get_normalizer()
    taxonomy = normalizer.get_taxonomy()

    # Count total skills
    total = 0
    for cat_data in taxonomy.get("categories", {}).values():
        total += len(cat_data.get("skills", []))
        for children in cat_data.get("children", {}).values():
            total += len(children)

    return SkillTaxonomyResponse(
        categories=taxonomy.get("categories", {}),
        total_skills=total,
    )
