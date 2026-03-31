"""
Chat / AI Assistant API endpoint.
POST /api/v1/chat — Semantic search over candidates + RAG-style responses.

Primary path : vector similarity search via LangChain / ChromaDB
Fallback path : keyword search against SQLite when vector store is unavailable
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security_auth import get_current_user
from app.models.user import User
from app.models.candidate import Candidate
from app.models.resume import Resume
from app.models.job import Job
from app.api.v1.schemas import ChatMessage, ChatResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["AI Assistant"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _vector_search(query: str, k: int = 5):
    """Try vector search; return empty list if store unavailable."""
    try:
        from app.services.vector_store import search_candidates
        return search_candidates(query, k=k)
    except Exception as e:
        logger.warning(f"Vector search unavailable: {e}")
        return []


def _keyword_fallback(query: str, db: Session):
    """Fallback: scan candidates from DB for keyword matches."""
    candidates = db.query(Candidate).all()
    query_lower = query.lower()
    results = []
    for c in candidates:
        resume = db.query(Resume).filter(Resume.candidate_id == c.id).order_by(Resume.created_at.desc()).first()
        skills = []
        if resume and resume.parsed_data:
            skills = resume.parsed_data.get("skills", [])
        skill_str = ", ".join(skills)
        if any(word in skill_str.lower() or word in (c.name or "").lower() for word in query_lower.split()):
            results.append({
                "candidate_id": c.id,
                "name": c.name or "Unknown",
                "email": c.email or "",
                "skills": skill_str,
                "score": 0.5,
            })
    return results


# ── Endpoint ──────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask the AI assistant",
    description=(
        "Natural language queries over candidates using semantic vector search. "
        "Examples: 'Find Python developers with ML experience', "
        "'Who has Docker and Kubernetes?', 'Show me senior engineers'"
    ),
)
def chat(
    msg: ChatMessage,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = msg.message.strip()
    context = msg.context or {}
    query_lower = query.lower()

    # ── Skill gap analysis (needs candidate_id + job_id in context) ───────
    candidate_id = context.get("candidate_id")
    job_id = context.get("job_id")
    if candidate_id and job_id and any(kw in query_lower for kw in ["gap", "missing", "match", "skill"]):
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        job = db.query(Job).filter(Job.id == job_id).first()
        if not candidate or not job:
            return ChatResponse(reply="Candidate or job not found.", sources=[])

        resume = db.query(Resume).filter(Resume.candidate_id == candidate_id).order_by(Resume.created_at.desc()).first()
        if not resume or not resume.parsed_data:
            return ChatResponse(reply=f"No parsed resume found for candidate {candidate_id}.", sources=[])

        candidate_skills = set(s.lower() for s in resume.parsed_data.get("skills", []))
        required = job.required_skills or []
        optional = job.optional_skills or []
        missing_req = [s for s in required if s.lower() not in candidate_skills]
        missing_opt = [s for s in optional if s.lower() not in candidate_skills]
        matching = [s for s in required if s.lower() in candidate_skills]

        reply = (
            f"**Skill gap — {candidate.name} → {job.title} at {job.company}:**\n\n"
            f"✅ Matching required ({len(matching)}): {', '.join(matching) or 'none'}\n"
            f"⚠️ Missing required ({len(missing_req)}): {', '.join(missing_req) or 'none'}\n"
            f"💡 Missing optional ({len(missing_opt)}): {', '.join(missing_opt[:5]) or 'none'}"
        )
        return ChatResponse(reply=reply, sources=[f"candidate:{candidate_id}", f"job:{job_id}"])

    # ── Job list ───────────────────────────────────────────────────────────
    if any(kw in query_lower for kw in ["job", "position", "role", "opening", "vacancy"]):
        jobs = db.query(Job).order_by(Job.created_at.desc()).limit(10).all()
        if not jobs:
            return ChatResponse(reply="No jobs saved yet. POST to /api/v1/jobs to add job descriptions.", sources=[])
        lines = [
            f"• **{j.title}** at {j.company or 'N/A'} "
            f"({j.experience_min}–{j.experience_max} yrs) — "
            f"Required: {', '.join((j.required_skills or [])[:5])}"
            for j in jobs
        ]
        return ChatResponse(
            reply=f"Saved jobs ({len(jobs)}):\n\n" + "\n".join(lines),
            sources=[f"job:{j.id}" for j in jobs],
        )

    # ── Semantic candidate search (primary path) ───────────────────────────
    if any(kw in query_lower for kw in [
        "find", "who", "show", "list", "candidate", "developer", "engineer",
        "with", "knows", "has", "experience", "skill",
    ]):
        # 1. Try vector search
        vector_results = _vector_search(query, k=8)

        # 2. Fall back to keyword search if vector store is empty or unavailable
        if not vector_results:
            logger.info("Vector store empty or unavailable, using keyword fallback")
            vector_results = _keyword_fallback(query, db)

        if not vector_results:
            total = db.query(Candidate).count()
            if total == 0:
                return ChatResponse(
                    reply="No candidates in the database yet. Upload resumes via POST /api/v1/parse first.",
                    sources=["database"],
                )
            return ChatResponse(
                reply=f"No candidates matched your query. There are {total} total candidate(s) in the database.",
                sources=["vector_store"],
            )

        lines = []
        sources = []
        for r in vector_results:
            score_pct = int(r["score"] * 100)
            skills_preview = r["skills"][:80] + ("..." if len(r["skills"]) > 80 else "")
            lines.append(
                f"• **{r['name']}** ({r['email']}) — Match: {score_pct}%\n"
                f"  Skills: {skills_preview or 'none listed'}"
            )
            if r.get("candidate_id"):
                sources.append(f"candidate:{r['candidate_id']}")

        reply = f"Found {len(lines)} candidate(s) for **\"{query}\"**:\n\n" + "\n\n".join(lines)
        return ChatResponse(reply=reply, sources=sources)

    # ── Help / taxonomy ────────────────────────────────────────────────────
    if any(kw in query_lower for kw in ["help", "what can", "how", "taxonomy", "skill category"]):
        return ChatResponse(
            reply=(
                "I'm the ResuMatch AI assistant backed by a **semantic vector search** over all parsed resumes.\n\n"
                "Try asking:\n"
                "• `Find Python developers with ML experience`\n"
                "• `Who knows Docker and Kubernetes?`\n"
                "• `Show me candidates with React skills`\n"
                "• `List all jobs`\n"
                "• `Skill gap` (provide `candidate_id` + `job_id` in the context field)\n\n"
                "Candidates are indexed automatically when you upload a resume."
            ),
            sources=[],
        )

    # ── Generic fallback: treat whole query as a semantic search ──────────
    vector_results = _vector_search(query, k=5)
    if vector_results:
        lines = [
            f"• **{r['name']}** — {r['skills'][:60]}"
            for r in vector_results
        ]
        return ChatResponse(
            reply=f"Here are the most relevant candidates for **\"{query}\"**:\n\n" + "\n".join(lines),
            sources=[f"candidate:{r['candidate_id']}" for r in vector_results if r.get("candidate_id")],
        )

    return ChatResponse(
        reply=(
            "I couldn't find a specific answer. Try:\n"
            "• `Find [skill] developers`\n"
            "• `Who knows [technology]?`\n"
            "• `List all candidates`\n"
            "• `Show jobs`"
        ),
        sources=[],
    )
