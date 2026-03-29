"""
Resume files endpoint.
GET /api/v1/resume/{id}
"""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security_auth import get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.models.resume import Resume

router = APIRouter(prefix="/resume", tags=["Resumes"])

@router.get("/{resume_id}")
def get_resume_file(
    resume_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
        
    settings = get_settings()
    file_path = os.path.join(settings.UPLOAD_DIR, resume.filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Resume file not found on disk")
        
    return FileResponse(file_path)
