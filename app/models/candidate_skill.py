"""
CandidateSkill junction model — links candidates to their normalized skills.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)  # Null if skill is unknown
    skill_name = Column(String(255), nullable=False)  # Original or normalized name
    proficiency_level = Column(Float, nullable=True)  # 0.0 - 1.0 estimated proficiency
    years_experience = Column(Float, nullable=True)
    source = Column(String(50), default="resume")  # resume, inferred, manual
    is_normalized = Column(Integer, default=0)  # 0 = raw, 1 = normalized
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="skills")
    skill = relationship("Skill", back_populates="candidate_skills")

    def __repr__(self):
        return f"<CandidateSkill(candidate_id={self.candidate_id}, skill='{self.skill_name}', proficiency={self.proficiency_level})>"
