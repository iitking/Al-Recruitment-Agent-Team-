from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CandidateAvailabilityRequest(BaseModel):
    available_dates: List[str] = Field(..., description="List of dates (YYYY-MM-DD)")
    preferred_times: List[str] = Field(default_factory=lambda: ["morning", "afternoon"])
    timezone: Optional[str] = "UTC"
    notes: Optional[str] = None

class InterviewSlot(BaseModel):
    start_time: datetime
    end_time: datetime
    timezone: str = "UTC"
    interviewer_email: str
    is_available: bool = True

class SlotSuggestionRequest(BaseModel):
    candidate_id: str
    interviewer_email: Optional[str] = "interviewer@company.com"
    duration_minutes: int = 45
    days_ahead: int = 5

class SlotSuggestionResponse(BaseModel):
    candidate_id: str
    interviewer_email: str
    suggested_slots: List[InterviewSlot]

class InterviewCreateRequest(BaseModel):
    candidate_id: str
    interviewer_email: str = Field(..., description="Interviewer email")
    start_time: datetime
    end_time: datetime
    timezone: Optional[str] = "UTC"
    title: Optional[str] = "Technical Screen Interview"
    idempotency_key: Optional[str] = None
    notes: Optional[str] = None

class InterviewUpdateRequest(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[str] = None # scheduled, completed, cancelled, rescheduled
    notes: Optional[str] = None

class InterviewResponse(BaseModel):
    id: str
    candidate_id: str
    interviewer_email: str
    candidate_email: str
    start_time: datetime
    end_time: datetime
    timezone: str
    title: str
    meeting_link: Optional[str]
    calendar_event_id: Optional[str]
    status: str
    idempotency_key: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
