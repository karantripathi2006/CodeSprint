"""
MatchResult model — stores the output of candidate-job matching.
"""

from sqlalchemy import Column, Integer, Float, Text, ForeignKey, DateTime, JSON, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    overall_score = Column(Float, nullable=False)       # 0.0 - 100.0
    skill_score = Column(Float, nullable=True)           # Skill-based component
    experience_score = Column(Float, nullable=True)      # Experience-based component
    education_score = Column(Float, nullable=True)       # Education-based component
    semantic_score = Column(Float, nullable=True)        # Embedding similarity score
    matching_skills = Column(JSON, nullable=True)        # Skills that matched
    missing_skills = Column(JSON, nullable=True)         # Required skills candidate lacks
    optional_missing = Column(JSON, nullable=True)       # Optional skills candidate lacks
    explanation = Column(Text, nullable=True)             # Human-readable match explanation
    recommendations = Column(JSON, nullable=True)        # Skill gap recommendations
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="match_results")
    job = relationship("Job", back_populates="match_results")

    def __repr__(self):
        return f"<MatchResult(candidate_id={self.candidate_id}, job_id={self.job_id}, score={self.overall_score})>"
