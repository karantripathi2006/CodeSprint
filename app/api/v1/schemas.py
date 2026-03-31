"""
Pydantic schemas for API request/response models.
Provides type-safe validation for all REST API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTH MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class UserCreate(BaseModel):
    username: str = Field(..., example="hr_admin")
    password: str = Field(..., example="securepassword")

class UserResponse(BaseModel):
    id: int
    username: str
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# ═══════════════════════════════════════════════════════════════════════════════
#  RESPONSE MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class EducationEntry(BaseModel):
    degree: str = ""
    institution: str = ""
    year: str = ""
    gpa: str = ""


class ExperienceEntry(BaseModel):
    company: str = ""
    role: str = ""
    duration: str = ""
    start_date: str = ""
    end_date: str = ""
    responsibilities: List[str] = []


class ProjectEntry(BaseModel):
    name: str = ""
    description: str = ""
    technologies: str = ""


class ParsedResume(BaseModel):
    """Response model for parsed resume data."""
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    summary: str = ""
    education: List[EducationEntry] = []
    experience: List[ExperienceEntry] = []
    skills: List[str] = []
    projects: List[ProjectEntry] = []
    certifications: List[str] = []
    parsing_time_ms: int = 0


class NormalizedSkills(BaseModel):
    """Response model for normalized skill data."""
    normalized_skills: List[str] = []
    inferred_skills: List[str] = []
    unknown_skills: List[str] = []
    all_skills: List[str] = []
    proficiency_map: Dict[str, float] = {}
    total_count: int = 0


class ResumeProcessingResult(BaseModel):
    """Full response for resume processing (parse + normalize)."""
    status: str = "success"
    candidate_id: Optional[int] = None
    filename: str = ""
    parsed_data: Optional[ParsedResume] = None
    normalized_skills: Optional[NormalizedSkills] = None
    errors: List[str] = []
    metadata: Dict[str, Any] = {}


class BatchProcessingResult(BaseModel):
    """Response for batch resume processing."""
    task_id: Optional[str] = None
    status: str = "processing"
    total: int = 0
    successful: int = 0
    failed: int = 0
    total_time_ms: int = 0
    results: List[ResumeProcessingResult] = []


# ═══════════════════════════════════════════════════════════════════════════════
#  MATCHING MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class JobDescriptionInput(BaseModel):
    """Input model for job description in matching."""
    title: str = Field(..., description="Job title", example="Senior Python Developer")
    company: str = Field("", description="Company name", example="TechCorp")
    description: str = Field(..., description="Full job description")
    required_skills: List[str] = Field([], description="Required skills", example=["Python", "FastAPI", "PostgreSQL"])
    optional_skills: List[str] = Field([], description="Nice-to-have skills", example=["Docker", "AWS"])
    experience_min: float = Field(0, description="Minimum years of experience", example=3)
    experience_max: float = Field(0, description="Maximum years of experience", example=7)
    location: str = ""
    job_type: str = ""


class MatchRequest(BaseModel):
    """Request model for matching endpoint."""
    candidate_id: Optional[int] = Field(None, description="Existing candidate ID to match")
    candidate_profile: Optional[Dict[str, Any]] = Field(None, description="Or provide candidate profile directly")
    job_description: JobDescriptionInput


class SkillRecommendation(BaseModel):
    """A single skill gap recommendation."""
    skill: str
    priority: str  # high, medium, low
    suggestion: str


class MatchResponse(BaseModel):
    """Response model for a single matching result."""
    candidate_id: Optional[int] = None
    name: str = ""
    email: str = ""
    skills: List[str] = []
    
    status: str = "success"
    overall_score: float = Field(0, description="Overall match score 0-100")
    skill_score: float = Field(0, description="Skill component score 0-100")
    experience_score: float = Field(0, description="Experience component score 0-100")
    semantic_score: float = Field(0, description="Semantic similarity score 0-100")
    matching_skills: List[str] = []
    missing_skills: List[str] = []
    optional_missing: List[str] = []
    explanation: str = ""
    recommendations: List[SkillRecommendation] = []
    match_time_ms: int = 0
    resume_id: Optional[int] = None

class MatchListResponse(BaseModel):
    """Response model for batch matching multiple candidates against a job."""
    matches: List[MatchResponse]
    total_evaluated: int


# ═══════════════════════════════════════════════════════════════════════════════
#  CANDIDATE / SKILLS MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class CandidateSummary(BaseModel):
    id: int
    name: str = ""
    email: str = ""
    skills: str = ""  # Comma separated
    resume_id: Optional[int] = None

class CandidateListResponse(BaseModel):
    candidates: List[CandidateSummary]
    total: int

class CandidateSkillResponse(BaseModel):
    """Response for candidate skills endpoint."""
    candidate_id: int
    candidate_name: str = ""
    total_skills: int = 0
    skills: List[Dict[str, Any]] = []


class SkillTaxonomyResponse(BaseModel):
    """Response for skill taxonomy endpoint."""
    categories: Dict[str, Any] = {}
    total_skills: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
#  JOB MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class JobResponse(BaseModel):
    """Response model for a saved job."""
    id: int
    title: str
    company: str
    description: str
    required_skills: List[str] = []
    optional_skills: List[str] = []
    experience_min: float = 0
    experience_max: float = 0
    location: str = ""
    job_type: str = ""

    class Config:
        from_attributes = True

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int


# ═══════════════════════════════════════════════════════════════════════════════
#  TASK STATUS MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # pending, started, success, failure, unknown
    result: Optional[Any] = None
    error: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
#  CHAT MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class ChatMessage(BaseModel):
    message: str = Field(..., description="User message to the AI assistant")
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context (candidate_id, job_id)")

class ChatResponse(BaseModel):
    reply: str
    sources: List[str] = []
    mode: str = "assistant"
    provider: str = "rules"


# ═══════════════════════════════════════════════════════════════════════════════
#  COMMON MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    status_code: int = 400


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = ""
    database: str = "connected"
    redis: str = "unknown"
