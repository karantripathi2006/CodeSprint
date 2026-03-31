"""
Communication Agent
===================
Drafts candidate-facing communications with Groq when configured and falls
back to deterministic templates when the API is unavailable.
"""

import json
import logging
from typing import Any, Dict, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class CommunicationAgent:
    """Generate outreach and interview communication drafts for recruiters."""

    EXPLICIT_PATTERNS = (
        "draft email",
        "write email",
        "compose email",
        "generate email",
        "prepare email",
        "send email",
        "email candidate",
        "draft message",
        "write message",
        "compose message",
        "candidate outreach",
        "contact candidate",
        "reach out",
        "follow up",
        "follow-up",
        "followup",
        "interview email",
        "interview invite",
        "interview invitation",
        "invite candidate",
        "rejection email",
        "offer letter",
        "communication draft",
    )

    ACTION_TERMS = ("draft", "write", "compose", "generate", "prepare", "create", "send")
    COMMUNICATION_TERMS = (
        "email",
        "mail",
        "message",
        "outreach",
        "communication",
        "invite",
        "follow up",
        "follow-up",
        "followup",
        "rejection",
        "offer",
    )

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.GROQ_API_KEY.strip()
        self.model = (settings.GROQ_MODEL or "llama-3.1-8b-instant").strip()
        self.timeout_s = max(int(settings.GROQ_TIMEOUT_S), 5)
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    def supports(self, query: str) -> bool:
        """Return True when a user message looks like a drafting request."""
        query_lower = (query or "").lower()
        if any(pattern in query_lower for pattern in self.EXPLICIT_PATTERNS):
            return True
        return (
            any(term in query_lower for term in self.ACTION_TERMS)
            and any(term in query_lower for term in self.COMMUNICATION_TERMS)
        )

    def generate(
        self,
        query: str,
        candidate: Optional[Dict[str, Any]] = None,
        job: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate a communication draft, preferring Groq when configured."""
        communication_type = self._infer_type(query)

        if self.api_key:
            try:
                reply = self._generate_with_groq(query, communication_type, candidate, job)
                return {
                    "reply": reply,
                    "provider": "groq",
                    "communication_type": communication_type,
                    "used_fallback": False,
                }
            except Exception as exc:
                logger.warning("Groq communication generation failed: %s", exc)

        return {
            "reply": self._build_fallback(query, communication_type, candidate, job),
            "provider": "template",
            "communication_type": communication_type,
            "used_fallback": True,
        }

    def _infer_type(self, query: str) -> str:
        """Classify the communication request into a simple workflow."""
        query_lower = (query or "").lower()

        if any(term in query_lower for term in ("reject", "rejection", "decline", "not moving forward")):
            return "rejection"
        if any(term in query_lower for term in ("follow up", "follow-up", "followup", "checking in", "reminder")):
            return "follow_up"
        if any(term in query_lower for term in ("interview", "screen", "schedule", "availability", "invite")):
            return "interview_invite"
        if any(term in query_lower for term in ("shortlist", "shortlisted", "selected", "opportunity", "outreach")):
            return "shortlist_outreach"
        return "general"

    def _generate_with_groq(
        self,
        query: str,
        communication_type: str,
        candidate: Optional[Dict[str, Any]],
        job: Optional[Dict[str, Any]],
    ) -> str:
        """Call Groq's OpenAI-compatible chat completions endpoint."""
        payload = {
            "model": self.model,
            "temperature": 0.4,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a recruitment communications agent. Draft polished, concise, "
                        "professional recruiter messages. Use only the provided context. "
                        "Do not invent compensation, interview panels, dates, or links. "
                        "Return markdown with exactly two sections: "
                        "**Subject:** on one line and **Body:** with the full message below it."
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_prompt(query, communication_type, candidate, job),
                },
            ],
        }

        req = urllib_request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib_request.urlopen(req, timeout=self.timeout_s) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib_error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Groq HTTP {exc.code}: {details}") from exc
        except urllib_error.URLError as exc:
            raise RuntimeError(f"Groq connection failed: {exc.reason}") from exc

        content = (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()
        if not content:
            raise RuntimeError("Groq returned an empty draft")
        return content

    def _build_prompt(
        self,
        query: str,
        communication_type: str,
        candidate: Optional[Dict[str, Any]],
        job: Optional[Dict[str, Any]],
    ) -> str:
        """Build a compact structured prompt for the LLM."""
        candidate_lines = self._format_candidate(candidate)
        job_lines = self._format_job(job)
        return (
            f"User request:\n{query.strip()}\n\n"
            f"Communication type: {communication_type}\n\n"
            f"Candidate context:\n{candidate_lines}\n\n"
            f"Job context:\n{job_lines}\n\n"
            "Keep the tone warm and professional. Mention only facts present in the context. "
            "If any detail is missing, keep the wording generic rather than inventing it."
        )

    def _format_candidate(self, candidate: Optional[Dict[str, Any]]) -> str:
        """Serialize candidate data for prompting."""
        if not candidate:
            return "- No candidate context supplied"

        skills = ", ".join(candidate.get("skills") or []) or "Not provided"
        experiences = candidate.get("experience") or []
        experience_lines = []
        for item in experiences[:3]:
            if isinstance(item, dict):
                role = item.get("role") or "Role"
                company = item.get("company") or "Company"
                duration = item.get("duration") or ""
                experience_lines.append(f"{role} at {company}{f' ({duration})' if duration else ''}")
        experience_summary = "; ".join(experience_lines) or "Not provided"

        return (
            f"- Name: {candidate.get('name') or 'Unknown'}\n"
            f"- Email: {candidate.get('email') or 'Not provided'}\n"
            f"- Location: {candidate.get('location') or 'Not provided'}\n"
            f"- Summary: {candidate.get('summary') or 'Not provided'}\n"
            f"- Skills: {skills}\n"
            f"- Recent experience: {experience_summary}"
        )

    def _format_job(self, job: Optional[Dict[str, Any]]) -> str:
        """Serialize job data for prompting."""
        if not job:
            return "- No job context supplied"

        required_skills = ", ".join(job.get("required_skills") or []) or "Not provided"
        optional_skills = ", ".join(job.get("optional_skills") or []) or "Not provided"
        return (
            f"- Title: {job.get('title') or 'Unknown'}\n"
            f"- Company: {job.get('company') or 'Not provided'}\n"
            f"- Location: {job.get('location') or 'Not provided'}\n"
            f"- Job type: {job.get('job_type') or 'Not provided'}\n"
            f"- Experience range: {job.get('experience_range') or 'Not provided'}\n"
            f"- Required skills: {required_skills}\n"
            f"- Optional skills: {optional_skills}"
        )

    def _build_fallback(
        self,
        query: str,
        communication_type: str,
        candidate: Optional[Dict[str, Any]],
        job: Optional[Dict[str, Any]],
    ) -> str:
        """Return a deterministic draft when Groq is unavailable."""
        candidate_name = (candidate or {}).get("name") or "Candidate"
        company = (job or {}).get("company") or "our team"
        job_title = (job or {}).get("title") or "the role"
        skills = (candidate or {}).get("skills") or []
        skills_line = ""
        if skills:
            skills_line = f" Your background in {', '.join(skills[:3])} especially stood out to us."

        if communication_type == "rejection":
            subject = f"Update on Your Application for {job_title}"
            body = (
                f"Dear {candidate_name},\n\n"
                f"Thank you for your interest in {job_title} at {company}. "
                "We appreciate the time you invested in the process.\n\n"
                "After careful review, we have decided not to move forward with your application at this stage. "
                "We will keep your profile in mind for future opportunities that may be a closer fit.\n\n"
                "Best regards,\nHiring Team"
            )
        elif communication_type == "follow_up":
            subject = f"Following Up on the {job_title} Opportunity"
            body = (
                f"Dear {candidate_name},\n\n"
                f"I wanted to follow up regarding the {job_title} opportunity with {company}.{skills_line}\n\n"
                "If you are still interested, please reply with your availability and any questions you may have. "
                "We would be glad to continue the conversation.\n\n"
                "Best regards,\nHiring Team"
            )
        elif communication_type == "interview_invite":
            subject = f"Interview Invitation - {job_title}"
            body = (
                f"Dear {candidate_name},\n\n"
                f"Thank you for your interest in {job_title} at {company}.{skills_line}\n\n"
                "We would like to invite you to a conversation to learn more about your background and discuss the role in more detail. "
                "Please share your availability over the next few days, and we will coordinate a suitable time.\n\n"
                "Best regards,\nHiring Team"
            )
        else:
            subject = f"Opportunity to Connect About {job_title}"
            body = (
                f"Dear {candidate_name},\n\n"
                f"I am reaching out regarding {job_title} at {company}.{skills_line}\n\n"
                "Your profile looks aligned with what we are hiring for, and we would welcome a quick conversation to explore fit and next steps. "
                "Please let us know if you would be open to connecting.\n\n"
                "Best regards,\nHiring Team"
            )

        preface = ""
        if not candidate and not job:
            preface = "I used a neutral template because no candidate or job context was provided.\n\n"
        elif not candidate or not job:
            preface = "I used the available context and kept the missing details generic.\n\n"

        if query.strip():
            preface += f"_Draft intent: {query.strip()}_\n\n"

        return f"{preface}**Subject:** {subject}\n\n**Body:**\n{body}"
