from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class WorkflowEventResponse(BaseModel):
    id: str
    candidate_id: str
    job_id: Optional[str]
    previous_status: Optional[str]
    new_status: str
    actor_type: str
    event_type: str
    details: Dict[str, Any]
    timestamp: datetime

    class Config:
        from_attributes = True

class DashboardSummaryResponse(BaseModel):
    total_jobs: int
    active_jobs: int
    total_candidates: int
    candidates_by_status: Dict[str, int]
    avg_screening_score: Optional[float]
    flagged_candidates_count: int
    scheduled_interviews_count: int
    recent_events: List[WorkflowEventResponse]
