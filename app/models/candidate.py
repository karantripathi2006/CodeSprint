"""
Candidate model — stores extracted candidate information.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    raw_resume_text = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Candidate(id={self.id}, name='{self.name}', email='{self.email}')>"
