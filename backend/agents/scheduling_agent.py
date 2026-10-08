from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.services.calendar_service import calendar_service

class SchedulingAgent:
    """
    Coordinates interview availability, suggests slots, and books calendar events.
    """

    def suggest_slots(
        self,
        interviewer_email: str,
        duration_minutes: int = 45,
        days_ahead: int = 5
    ) -> List[Dict[str, Any]]:
        return calendar_service.suggest_slots(
            interviewer_email=interviewer_email,
            duration_minutes=duration_minutes,
            days_ahead=days_ahead
        )

    def schedule_interview(
        self,
        candidate_email: str,
        interviewer_email: str,
        start_time: datetime,
        end_time: datetime,
        title: str = "Candidate Technical Screen",
        timezone: str = "UTC",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        return calendar_service.create_event(
            candidate_email=candidate_email,
            interviewer_email=interviewer_email,
            start_time=start_time,
            end_time=end_time,
            title=title,
            timezone=timezone,
            idempotency_key=idempotency_key
        )

    def cancel_interview(self, calendar_event_id: str) -> bool:
        return calendar_service.cancel_event(calendar_event_id)

scheduling_agent = SchedulingAgent()
