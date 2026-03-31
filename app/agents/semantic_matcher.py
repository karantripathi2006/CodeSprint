"""
Semantic Matching Agent
=======================
Performs intelligent matching between candidate profiles and job descriptions
using sentence-transformer embeddings and weighted multi-factor scoring.
"""

import logging
import re
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# ── Lazy-loaded embedding model (singleton) ──────────────────────────────────
_model = None


def _get_model():
    """Load the sentence-transformer model once (lazy singleton)."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            from app.core.config import get_settings
            settings = get_settings()
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            _model = None
    return _model


class SemanticMatcherAgent:
    """
    Agent responsible for matching candidates against job descriptions.
    
    Scoring Components:
    - Skill Match Score (50%): required + optional skill overlap
    - Experience Score (30%): years of experience vs requirements
    - Semantic Similarity (20%): embedding cosine similarity
    
    Outputs:
    - Overall match score (0-100)
    - Detailed score breakdown
    - Matching and missing skills
    - Human-readable explanation
    - Skill gap recommendations
    """

    def __init__(self, skill_weight: float = 0.50, experience_weight: float = 0.30,
                 semantic_weight: float = 0.20):
        """Initialize with configurable scoring weights."""
        self.skill_weight = skill_weight
        self.experience_weight = experience_weight
        self.semantic_weight = semantic_weight

    def match(self, candidate_profile: Dict[str, Any], job_description: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match a candidate profile against a job description.
        
        Args:
            candidate_profile: Parsed + normalized candidate data
                Expected keys: name, skills (with normalized_skills), experience, education, summary
            job_description: Job requirements
                Expected keys: title, description, required_skills, optional_skills,
                               experience_min, experience_max
                               
        Returns:
            Dict with: overall_score, skill_score, experience_score, semantic_score,
                       matching_skills, missing_skills, optional_missing,
                       explanation, recommendations
        """
        start_time = time.time()
        logger.info(f"Matching candidate against job: {job_description.get('title', 'Unknown')}")

        # 1. Compute Skill Match Score
        skill_result = self._compute_skill_score(candidate_profile, job_description)

        # 2. Compute Experience Score
        experience_score = self._compute_experience_score(candidate_profile, job_description)

        # 3. Compute Semantic Similarity Score
        semantic_score = self._compute_semantic_score(candidate_profile, job_description)

        # 4. Calculate weighted overall score
        overall_score = round(
            (skill_result["score"] * self.skill_weight +
             experience_score * self.experience_weight +
             semantic_score * self.semantic_weight) * 100,
            1
        )
        overall_score = max(0, min(100, overall_score))

        # 5. Generate explanation and recommendations
        explanation = self._generate_explanation(
            overall_score, skill_result, experience_score, semantic_score,
            candidate_profile, job_description
        )
        recommendations = self._generate_recommendations(
            skill_result["missing_required"], skill_result["missing_optional"]
        )

        result = {
            "overall_score": overall_score,
            "skill_score": round(skill_result["score"] * 100, 1),
            "experience_score": round(experience_score * 100, 1),
            "semantic_score": round(semantic_score * 100, 1),
            "matching_skills": skill_result["matching"],
            "missing_skills": skill_result["missing_required"],
            "optional_missing": skill_result["missing_optional"],
            "explanation": explanation,
            "recommendations": recommendations,
            "match_time_ms": int((time.time() - start_time) * 1000),
        }

        logger.info(f"Match complete: score={overall_score}, "
                     f"matched={len(skill_result['matching'])}/{len(job_description.get('required_skills', []))} required skills")
        return result

    # ═══════════════════════════════════════════════════════════════════════
    #  SKILL SCORING
    # ═══════════════════════════════════════════════════════════════════════

    def _compute_skill_score(self, candidate: Dict, job: Dict) -> Dict[str, Any]:
        """
        Compute skill-based match score.
        Required skills are weighted 2x compared to optional skills.
        """
        # Get candidate skills (normalized + inferred + unknown)
        skills_data = candidate.get("skills", {})
        if isinstance(skills_data, dict):
            candidate_skills = set(s.lower() for s in skills_data.get("all_skills", []))
        elif isinstance(skills_data, list):
            candidate_skills = set(s.lower() for s in skills_data)
        else:
            candidate_skills = set()

        required = [s for s in job.get("required_skills", []) if s]
        optional = [s for s in job.get("optional_skills", []) if s]

        # Find matching/missing required skills
        matching_required = [s for s in required if s.lower() in candidate_skills]
        missing_required = [s for s in required if s.lower() not in candidate_skills]

        # Find matching/missing optional skills
        matching_optional = [s for s in optional if s.lower() in candidate_skills]
        missing_optional = [s for s in optional if s.lower() not in candidate_skills]

        # Score: required skills count 2x
        total_weight = (len(required) * 2) + len(optional) if (required or optional) else 1
        matched_weight = (len(matching_required) * 2) + len(matching_optional)
        score = matched_weight / total_weight if total_weight > 0 else 0.5

        return {
            "score": min(1.0, score),
            "matching": matching_required + matching_optional,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "required_match_pct": len(matching_required) / len(required) * 100 if required else 100,
        }

    # ═══════════════════════════════════════════════════════════════════════
    #  EXPERIENCE SCORING
    # ═══════════════════════════════════════════════════════════════════════

    def _compute_experience_score(self, candidate: Dict, job: Dict) -> float:
        """Compute experience match score based on years of experience."""
        exp_min = job.get("experience_min", 0) or 0
        exp_max = job.get("experience_max", exp_min + 5) or (exp_min + 5)

        # Estimate candidate's total years of experience
        candidate_years = self._estimate_total_experience(candidate.get("experience", []))

        if exp_min == 0 and exp_max == 0:
            return 0.7  # No experience requirement → partial score

        if candidate_years >= exp_min:
            if candidate_years <= exp_max:
                return 1.0  # Perfect fit
            else:
                # Over-qualified (slight penalty)
                over = candidate_years - exp_max
                return max(0.6, 1.0 - (over * 0.05))
        else:
            # Under-qualified
            ratio = candidate_years / exp_min if exp_min > 0 else 0
            return max(0.1, ratio)

    def _estimate_total_experience(self, experiences: List[Dict]) -> float:
        """Estimate total years of experience from experience entries."""
        if not experiences:
            return 0

        total_years = 0
        for exp in experiences:
            duration = exp.get("duration", "")
            # Try to parse date ranges
            years = self._parse_duration_years(duration)
            if years > 0:
                total_years += years
            else:
                # Default: assume 1.5 years per entry
                total_years += 1.5

        return round(total_years, 1)

    def _parse_duration_years(self, duration_str: str) -> float:
        """Parse a duration string and return approximate years."""
        if not duration_str:
            return 0

        # Check for explicit year mentions
        year_match = re.findall(r"(\d{4})", duration_str)
        if len(year_match) >= 2:
            try:
                start_year = int(year_match[0])
                end_year = int(year_match[-1])
                if 1990 <= start_year <= 2030 and 1990 <= end_year <= 2030:
                    return max(0.5, end_year - start_year)
            except ValueError:
                pass

        # Check for "Present" or "Current"
        if re.search(r"present|current|now", duration_str, re.IGNORECASE):
            year_match = re.search(r"(\d{4})", duration_str)
            if year_match:
                start_year = int(year_match.group(1))
                return max(0.5, datetime.now().year - start_year)  # Current year

        return 0

    # ═══════════════════════════════════════════════════════════════════════
    #  SEMANTIC SCORING
    # ═══════════════════════════════════════════════════════════════════════

    def _compute_semantic_score(self, candidate: Dict, job: Dict) -> float:
        """
        Compute semantic similarity between candidate profile and job description
        using sentence-transformer embeddings.
        """
        model = _get_model()
        if model is None:
            logger.warning("Embedding model not available, using fallback text overlap scoring")
            return self._fallback_text_similarity(candidate, job)

        try:
            # Build candidate text representation
            candidate_text = self._build_candidate_text(candidate)
            job_text = self._build_job_text(job)

            # Encode both texts
            embeddings = model.encode([candidate_text, job_text], convert_to_tensor=True)

            # Compute cosine similarity
            from sentence_transformers.util import cos_sim
            similarity = cos_sim(embeddings[0], embeddings[1]).item()

            # Normalize from [-1, 1] to [0, 1]
            return max(0, min(1.0, (similarity + 1) / 2))

        except Exception as e:
            logger.error(f"Semantic scoring failed: {e}")
            return self._fallback_text_similarity(candidate, job)

    def _build_candidate_text(self, candidate: Dict) -> str:
        """Build a text representation of the candidate for embedding."""
        parts = []
        if candidate.get("summary"):
            parts.append(candidate["summary"])

        skills = candidate.get("skills", {})
        if isinstance(skills, dict):
            all_skills = skills.get("all_skills", [])
        elif isinstance(skills, list):
            all_skills = skills
        else:
            all_skills = []
        if all_skills:
            parts.append("Skills: " + ", ".join(all_skills))

        for exp in candidate.get("experience", [])[:3]:  # Top 3 experiences
            role = exp.get("role", "")
            company = exp.get("company", "")
            if role or company:
                parts.append(f"{role} at {company}")

        for edu in candidate.get("education", [])[:2]:
            degree = edu.get("degree", "")
            if degree:
                parts.append(degree)

        return " | ".join(parts) if parts else "No profile data"

    def _build_job_text(self, job: Dict) -> str:
        """Build a text representation of the job for embedding."""
        parts = []
        if job.get("title"):
            parts.append(job["title"])
        if job.get("description"):
            parts.append(job["description"][:500])  # Limit description length
        required = job.get("required_skills", [])
        if required:
            parts.append("Required: " + ", ".join(required))
        optional = job.get("optional_skills", [])
        if optional:
            parts.append("Nice to have: " + ", ".join(optional))
        return " | ".join(parts) if parts else "No job data"

    def _fallback_text_similarity(self, candidate: Dict, job: Dict) -> float:
        """Fallback text overlap when embeddings aren't available."""
        candidate_text = self._build_candidate_text(candidate).lower()
        job_text = self._build_job_text(job).lower()

        # Simple word overlap
        candidate_words = set(re.findall(r"\w+", candidate_text))
        job_words = set(re.findall(r"\w+", job_text))

        if not job_words:
            return 0.5

        overlap = candidate_words & job_words
        # Remove common stop words
        stopwords = {"the", "a", "an", "and", "or", "in", "at", "to", "for", "of", "with", "is", "are"}
        overlap -= stopwords

        return min(1.0, len(overlap) / max(len(job_words - stopwords), 1))

    # ═══════════════════════════════════════════════════════════════════════
    #  EXPLANATION GENERATION
    # ═══════════════════════════════════════════════════════════════════════

    def _generate_explanation(self, overall_score: float, skill_result: Dict,
                               experience_score: float, semantic_score: float,
                               candidate: Dict, job: Dict) -> str:
        """Generate a human-readable match explanation."""
        lines = []

        # Overall assessment
        if overall_score >= 80:
            lines.append(f"✅ Excellent match ({overall_score}%) — Candidate is highly qualified for this role.")
        elif overall_score >= 60:
            lines.append(f"🟡 Good match ({overall_score}%) — Candidate meets most requirements with some gaps.")
        elif overall_score >= 40:
            lines.append(f"🟠 Partial match ({overall_score}%) — Candidate has relevant skills but significant gaps exist.")
        else:
            lines.append(f"🔴 Low match ({overall_score}%) — Candidate may need substantial upskilling for this role.")

        # Skill breakdown
        matching = skill_result["matching"]
        missing_req = skill_result["missing_required"]
        if matching:
            lines.append(f"\n📋 Matching Skills ({len(matching)}): {', '.join(matching)}")
        if missing_req:
            lines.append(f"⚠️ Missing Required Skills ({len(missing_req)}): {', '.join(missing_req)}")

        # Experience
        exp_pct = round(experience_score * 100)
        lines.append(f"\n💼 Experience Fit: {exp_pct}%")

        # Semantic relevance
        sem_pct = round(semantic_score * 100)
        lines.append(f"🧠 Semantic Relevance: {sem_pct}%")

        return "\n".join(lines)

    def _generate_recommendations(self, missing_required: List[str],
                                    missing_optional: List[str]) -> List[Dict[str, str]]:
        """Generate skill gap recommendations."""
        recommendations = []

        for skill in missing_required:
            recommendations.append({
                "skill": skill,
                "priority": "high",
                "suggestion": f"Learn {skill} — this is a required skill for the role. "
                              f"Consider online courses, certifications, or personal projects.",
            })

        for skill in missing_optional[:5]:  # Limit optional recommendations
            recommendations.append({
                "skill": skill,
                "priority": "medium",
                "suggestion": f"Consider learning {skill} — it's listed as nice-to-have "
                              f"and would strengthen your profile.",
            })

        return recommendations
