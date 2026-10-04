from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class RequirementEvidence(BaseModel):
    requirement: str
    evidence: str
    confidence: Optional[float] = 1.0
    matched: bool = True

class MatchingReportResponse(BaseModel):
    id: str
    candidate_id: str
    job_id: str
    matched_requirements: List[RequirementEvidence] = Field(default_factory=list)
    missing_or_unclear_requirements: List[str] = Field(default_factory=list)
    match_score: Optional[float] = None
    rubric_breakdown: Dict[str, Any] = Field(default_factory=dict)
    recommendation: Optional[str] = None
    recommendation_rationale: Optional[str] = None
    review_flags: List[str] = Field(default_factory=list)
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RecruiterReviewRequest(BaseModel):
    decision: str = Field(..., description="approved, rejected, clarification_requested, or on_hold")
    recruiter_name: Optional[str] = "Recruiter"
    notes: Optional[str] = ""
    override: Optional[bool] = False

class RecruiterReviewResponse(BaseModel):
    id: str
    candidate_id: str
    decision: str
    recruiter_name: str
    notes: Optional[str]
    overridden: bool
    new_candidate_status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
