from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class ParsedProfile(BaseModel):
    skills: List[str] = Field(default_factory=list)
    experience_years: float = Field(0.0)
    education: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    employment_history: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    extraction_warnings: List[str] = Field(default_factory=list)
    needs_manual_review: bool = Field(False)

class CandidateProfileResponse(ParsedProfile):
    id: str
    candidate_id: str
    parsed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ResumeResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    parsing_status: str
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CandidateBase(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = "Applied"

class CandidateCreate(BaseModel):
    job_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class CandidateResponse(CandidateBase):
    id: str
    job_id: str
    created_at: datetime
    updated_at: datetime
    resume: Optional[ResumeResponse] = None
    profile: Optional[CandidateProfileResponse] = None
    latest_score: Optional[float] = None
    latest_recommendation: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
