"""
Chat / AI Assistant API endpoint.
POST /api/v1/chat - HR-assistant style responses over candidates + jobs.

Primary  : vector similarity search via LangChain / ChromaDB
Fallback  : keyword search against SQLite when vector store is unavailable
Optional  : Groq-backed communication drafting for recruiter outreach
"""

import logging
from typing import Any, Dict, Optional, Tuple

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.communication_agent import CommunicationAgent
from app.api.v1.schemas import ChatMessage, ChatResponse
from app.core.database import get_db
from app.core.security_auth import get_current_user
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["AI Assistant"])

_communication_agent: Optional[CommunicationAgent] = None


def get_communication_agent() -> CommunicationAgent:
    """Lazily initialize the communication agent."""
    global _communication_agent
    if _communication_agent is None:
        _communication_agent = CommunicationAgent()
    return _communication_agent


# - Helpers -------------------------------------------------------------------

def _vector_search(query: str, k: int = 5):
    try:
        from app.services.vector_store import search_candidates
        return search_candidates(query, k=k)
    except Exception as exc:
        logger.warning("Vector search unavailable: %s", exc)
        return []


def _keyword_fallback(query: str, db: Session):
    candidates = db.query(Candidate).all()
    query_lower = query.lower()
    results = []
    for candidate in candidates:
        resume = (
            db.query(Resume)
            .filter(Resume.candidate_id == candidate.id)
            .order_by(Resume.created_at.desc())
            .first()
        )
        skills = []
        if resume and resume.parsed_data:
            skills = resume.parsed_data.get("skills", [])
        skill_str = ", ".join(skills)
        if any(word in skill_str.lower() or word in (candidate.name or "").lower() for word in query_lower.split()):
            results.append(
                {
                    "candidate_id": candidate.id,
                    "name": candidate.name or "Unknown",
                    "email": candidate.email or "",
                    "skills": skill_str,
                    "score": 0.5,
                }
            )
    return results


def _format_candidate_list(results: list, query: str) -> str:
    if not results:
        return ""

    lines = []
    for result in results:
        score_pct = int(result["score"] * 100)
        skills_preview = result["skills"][:70] + ("..." if len(result["skills"]) > 70 else "")
        strength = "Strong match" if score_pct >= 80 else "Moderate match" if score_pct >= 60 else "Partial match"
        lines.append(
            f"**{result['name']}** ({result.get('email', '')})\n"
            f"  {strength} · {score_pct}% relevance\n"
            f"  Skills: {skills_preview or 'Not listed'}"
        )

    header = f'I found **{len(lines)} candidate(s)** relevant to "{query}":\n\n'
    footer = "\n\nWould you like to see a skill gap analysis for any of these candidates, or draft a message for the top match?"
    return header + "\n\n".join(lines) + footer


def _get_candidate_with_resume(db: Session, candidate_id: Optional[int]) -> Tuple[Optional[Candidate], Optional[Resume]]:
    """Load a candidate and their latest resume when context includes an ID."""
    if not candidate_id:
        return None, None

    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        return None, None

    resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == candidate_id)
        .order_by(Resume.created_at.desc())
        .first()
    )
    return candidate, resume


def _build_candidate_context(candidate: Optional[Candidate], resume: Optional[Resume]) -> Optional[Dict[str, Any]]:
    """Create a compact candidate context payload for the communication agent."""
    if not candidate:
        return None

    parsed = resume.parsed_data if resume and isinstance(resume.parsed_data, dict) else {}
    experience = parsed.get("experience", []) if isinstance(parsed, dict) else []
    if not isinstance(experience, list):
        experience = []

    skills = parsed.get("skills", []) if isinstance(parsed, dict) else []
    if not isinstance(skills, list):
        skills = []

    return {
        "id": candidate.id,
        "name": candidate.name or "Candidate",
        "email": candidate.email or "",
        "phone": candidate.phone or "",
        "location": candidate.location or "",
        "summary": candidate.summary or parsed.get("summary", ""),
        "skills": skills[:12],
        "experience": experience[:3],
    }


def _build_job_context(job: Optional[Job]) -> Optional[Dict[str, Any]]:
    """Create a compact job context payload for the communication agent."""
    if not job:
        return None

    experience_range = "Not provided"
    if job.experience_min is not None and job.experience_max is not None:
        experience_range = f"{job.experience_min:g}-{job.experience_max:g} years"
    elif job.experience_min is not None:
        experience_range = f"{job.experience_min:g}+ years"
    elif job.experience_max is not None:
        experience_range = f"Up to {job.experience_max:g} years"

    return {
        "id": job.id,
        "title": job.title,
        "company": job.company or "",
        "location": job.location or "",
        "job_type": job.job_type or "",
        "required_skills": (job.required_skills or [])[:10],
        "optional_skills": (job.optional_skills or [])[:6],
        "experience_range": experience_range,
    }


# - Endpoint ------------------------------------------------------------------

@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask the AI assistant",
)
def chat(
    msg: ChatMessage,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    query = msg.message.strip()
    if not query:
        return ChatResponse(reply="Please enter a message so I can help.", sources=[], mode="assistant", provider="rules")

    context = msg.context or {}
    query_lower = query.lower()
    candidate_id = context.get("candidate_id")
    job_id = context.get("job_id")

    candidate, resume = _get_candidate_with_resume(db, candidate_id)
    job = db.query(Job).filter(Job.id == job_id).first() if job_id else None

    communication_agent = get_communication_agent()
    if communication_agent.supports(query):
        missing_context = []
        if candidate_id and not candidate:
            missing_context.append("candidate")
        if job_id and not job:
            missing_context.append("job")

        if missing_context:
            missing_label = " and ".join(missing_context)
            return ChatResponse(
                reply=f"I couldn't locate the {missing_label} context for that communication draft. Please verify the IDs and try again.",
                sources=[],
                mode="communication",
                provider="rules",
            )

        draft = communication_agent.generate(
            query=query,
            candidate=_build_candidate_context(candidate, resume),
            job=_build_job_context(job),
        )
        sources = []
        if candidate:
            sources.append(f"candidate:{candidate.id}")
        if job:
            sources.append(f"job:{job.id}")
        sources.append(f"provider:{draft['provider']}")

        return ChatResponse(
            reply=draft["reply"],
            sources=sources,
            mode="communication",
            provider=draft["provider"],
        )

    # - Greeting --------------------------------------------------------------
    if any(kw in query_lower for kw in ["hello", "hi", "hey", "greet", "good morning", "good afternoon"]):
        total = db.query(Candidate).count()
        return ChatResponse(
            reply=(
                "Hello! I'm your AI Recruitment Assistant.\n\n"
                f"I currently have **{total} candidate(s)** in the system ready for analysis.\n\n"
                "Here's what I can help you with:\n"
                "• Search candidates by skill or role\n"
                "• Perform skill gap analysis against a job\n"
                "• Draft outreach, interview, or rejection emails\n"
                "• List and compare saved job postings\n"
                "• Upload a resume directly via the paperclip button\n\n"
                "How would you like to proceed?"
            ),
            sources=[],
        )

    # - Skill gap analysis ----------------------------------------------------
    if candidate_id and job_id and any(kw in query_lower for kw in ["gap", "missing", "match", "skill"]):
        if not candidate or not job:
            return ChatResponse(
                reply="I couldn't locate that candidate or job. Please verify the IDs and try again.",
                sources=[],
            )

        if not resume or not resume.parsed_data:
            return ChatResponse(
                reply=f"No parsed resume is on file for **{candidate.name}**. Please upload their CV first.",
                sources=[],
            )

        candidate_skills = set(skill.lower() for skill in resume.parsed_data.get("skills", []))
        required = job.required_skills or []
        optional = job.optional_skills or []
        missing_req = [skill for skill in required if skill.lower() not in candidate_skills]
        missing_opt = [skill for skill in optional if skill.lower() not in candidate_skills]
        matching = [skill for skill in required if skill.lower() in candidate_skills]
        match_pct = int((len(matching) / len(required) * 100)) if required else 0

        strength = "strong" if match_pct >= 80 else "moderate" if match_pct >= 60 else "limited"

        reply = (
            f"**Skill Gap Report - {candidate.name} -> {job.title}**\n\n"
            f"Overall alignment: **{match_pct}%** ({strength} match)\n\n"
            f"Matched required skills ({len(matching)}): {', '.join(matching) or 'None'}\n"
            f"Missing required skills ({len(missing_req)}): {', '.join(missing_req) or 'None'}\n"
            f"Missing optional skills ({len(missing_opt)}): {', '.join(missing_opt[:5]) or 'None'}\n\n"
        )
        if missing_req:
            reply += (
                f"I'd recommend probing the candidate on **{missing_req[0]}** during the interview "
                "to understand their learning curve."
            )
        else:
            reply += "This candidate meets all core requirements. Consider fast-tracking to the next stage."

        return ChatResponse(reply=reply, sources=[f"candidate:{candidate_id}", f"job:{job_id}"])

    # - Job list --------------------------------------------------------------
    if any(kw in query_lower for kw in ["job", "position", "role", "opening", "vacancy", "posting"]):
        jobs = db.query(Job).order_by(Job.created_at.desc()).limit(10).all()
        if not jobs:
            return ChatResponse(
                reply="No job postings have been saved yet. You can add one via **POST /api/v1/jobs** or through the Job Match page.",
                sources=[],
            )

        lines = [
            f"**{item.title}** at {item.company or 'N/A'} · "
            f"{item.experience_min}–{item.experience_max} yrs exp\n"
            f"  Required: {', '.join((item.required_skills or [])[:5]) or 'Not specified'}"
            for item in jobs
        ]
        return ChatResponse(
            reply=(
                f"Here are the **{len(jobs)} active job posting(s)**:\n\n"
                + "\n\n".join(lines)
                + "\n\nWould you like to match candidates against any of these roles or draft outreach for one of them?"
            ),
            sources=[f"job:{item.id}" for item in jobs],
        )

    # - List all candidates ---------------------------------------------------
    if any(kw in query_lower for kw in ["list all", "show all", "all candidates", "everyone"]):
        candidates = db.query(Candidate).order_by(Candidate.created_at.desc()).limit(10).all()
        if not candidates:
            return ChatResponse(
                reply="There are no candidates in the system yet. Upload a resume using the paperclip button to get started.",
                sources=[],
            )

        lines = [f"**{item.name}** - {item.email or 'No email'}" for item in candidates]
        return ChatResponse(
            reply=(
                f"I have **{len(candidates)} candidate(s)** on file:\n\n"
                + "\n".join(lines)
                + "\n\nYou can ask me about any of them, compare them to a job, or draft a message for one of them."
            ),
            sources=[f"candidate:{item.id}" for item in candidates],
        )

    # - Semantic candidate search --------------------------------------------
    if any(
        kw in query_lower
        for kw in [
            "find",
            "who",
            "show",
            "list",
            "candidate",
            "developer",
            "engineer",
            "with",
            "knows",
            "has",
            "experience",
            "skill",
            "looking for",
        ]
    ):
        vector_results = _vector_search(query, k=8)
        if not vector_results:
            vector_results = _keyword_fallback(query, db)

        if not vector_results:
            total = db.query(Candidate).count()
            if total == 0:
                return ChatResponse(
                    reply="No candidates are in the system yet. Please upload resumes via the paperclip button or the Resume Parser page.",
                    sources=["database"],
                )
            return ChatResponse(
                reply=f"No candidates matched that query. There are **{total} total candidate(s)** in the database - try broadening your search terms.",
                sources=["vector_store"],
            )

        formatted = _format_candidate_list(vector_results, query)
        return ChatResponse(
            reply=formatted,
            sources=[f"candidate:{item['candidate_id']}" for item in vector_results if item.get("candidate_id")],
        )

    # - Help -----------------------------------------------------------------
    if any(kw in query_lower for kw in ["help", "what can", "how", "what do", "capabilities"]):
        return ChatResponse(
            reply=(
                "I'm your AI Recruitment Assistant. Here's what I can do:\n\n"
                "**Candidate Search**\n"
                "• `Find Python developers with ML experience`\n"
                "• `Who knows Docker and Kubernetes?`\n\n"
                "**Job and Matching**\n"
                "• `List all jobs`\n"
                "• `Skill gap` (provide candidate_id + job_id in context)\n\n"
                "**Communication Drafts**\n"
                "• `Draft an interview email for candidate 12`\n"
                "• `Write a rejection email for the frontend role`\n\n"
                "**Resume Upload**\n"
                "• Click the paperclip icon to upload a PDF or DOCX - I'll extract and evaluate it instantly.\n\n"
                "What would you like to do?"
            ),
            sources=[],
        )

    # - Generic fallback ------------------------------------------------------
    vector_results = _vector_search(query, k=5)
    if vector_results:
        formatted = _format_candidate_list(vector_results, query)
        return ChatResponse(
            reply=formatted,
            sources=[f"candidate:{item['candidate_id']}" for item in vector_results if item.get("candidate_id")],
        )

    return ChatResponse(
        reply=(
            "I wasn't able to find a specific answer to that. Here are some things you can try:\n\n"
            "• `Find [skill] developers`\n"
            "• `Who knows [technology]?`\n"
            "• `List all candidates`\n"
            "• `Show jobs`\n"
            "• `Draft an interview email for this candidate`\n\n"
            "Or upload a resume using the paperclip button."
        ),
        sources=[],
    )
