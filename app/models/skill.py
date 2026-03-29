"""
Skill model — stores the skill taxonomy with hierarchical structure.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    category = Column(String(100), nullable=True)  # e.g., Programming, Framework, Cloud
    parent_skill_id = Column(Integer, ForeignKey("skills.id"), nullable=True)  # Hierarchical taxonomy
    created_at = Column(DateTime, server_default=func.now())

    # Self-referencing relationship for taxonomy tree
    parent = relationship("Skill", remote_side=[id], backref="children")
    candidate_skills = relationship("CandidateSkill", back_populates="skill")

    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}', category='{self.category}')>"
