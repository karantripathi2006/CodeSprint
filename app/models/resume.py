"""
Resume model — stores uploaded resume metadata and parsed data.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, nullable=True)  # bytes
    parsed_data = Column(JSON, nullable=True)  # Full structured parse result
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    candidate = relationship("Candidate", back_populates="resumes")

    def __repr__(self):
        return f"<Resume(id={self.id}, filename='{self.filename}', status='{self.status}')>"
