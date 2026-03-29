"""
Job model — stores job descriptions for matching.
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=True)   # ["Python", "FastAPI", ...]
    optional_skills = Column(JSON, nullable=True)   # ["Docker", "AWS", ...]
    experience_min = Column(Float, nullable=True)    # Minimum years of experience
    experience_max = Column(Float, nullable=True)    # Maximum years of experience
    location = Column(String(255), nullable=True)
    job_type = Column(String(50), nullable=True)     # full-time, part-time, contract
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    match_results = relationship("MatchResult", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job(id={self.id}, title='{self.title}', company='{self.company}')>"
