from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class JobBase(BaseModel):
    title: str = Field(..., description="Job title")
    department: Optional[str] = Field(None, description="Department name")
    description: str = Field(..., description="Full job description")
    required_skills: List[str] = Field(default_factory=list, description="Mandatory skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Bonus / preferred skills")
    min_experience_years: int = Field(0, ge=0, description="Minimum years of experience")
    rubric: Dict[str, float] = Field(
        default_factory=lambda: {"skills_weight": 0.5, "experience_weight": 0.3, "projects_weight": 0.2},
        description="Rubric weighting"
    )
    workflow_config: Dict[str, Any] = Field(
        default_factory=lambda: {"auto_approve_threshold": 80.0, "require_recruiter_review": True},
        description="Workflow automation settings"
    )

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    min_experience_years: Optional[int] = None
    rubric: Optional[Dict[str, float]] = None
    workflow_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class JobResponse(JobBase):
    id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    candidate_count: Optional[int] = 0
    model_config = ConfigDict(from_attributes=True)
