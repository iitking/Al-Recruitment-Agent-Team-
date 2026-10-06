import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class CalendarService:
    def __init__(self):
        # In-memory store of active calendar events
        self.booked_events: List[Dict[str, Any]] = []

    def suggest_slots(
        self,
        interviewer_email: str,
        duration_minutes: int = 45,
        days_ahead: int = 5,
        start_from: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculates upcoming available interview slots, avoiding existing bookings.
        """
        now = start_from or datetime.utcnow()
        # Default start tomorrow at 10:00 AM UTC
        start_date = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        
        suggested = []
        # Generate slots across the next few days (business hours: 10:00, 14:00, 16:00 UTC)
        for day_offset in range(days_ahead):
            current_day = start_date + timedelta(days=day_offset)
            # Skip weekends (Saturday=5, Sunday=6)
            if current_day.weekday() >= 5:
                continue

            for hour in [10, 14, 16]:
                slot_start = current_day.replace(hour=hour, minute=0)
                slot_end = slot_start + timedelta(minutes=duration_minutes)

                # Check conflict with existing events
                has_conflict = any(
                    evt["interviewer_email"] == interviewer_email and
                    evt["status"] == "scheduled" and
                    max(slot_start, evt["start_time"]) < min(slot_end, evt["end_time"])
                    for evt in self.booked_events
                )

                if not has_conflict:
                    suggested.append({
                        "start_time": slot_start,
                        "end_time": slot_end,
                        "timezone": "UTC",
                        "interviewer_email": interviewer_email,
                        "is_available": True
                    })

                if len(suggested) >= 6:
                    break
            if len(suggested) >= 6:
                break

        return suggested

    def create_event(
        self,
        candidate_email: str,
        interviewer_email: str,
        start_time: datetime,
        end_time: datetime,
        title: str = "Recruitment Interview",
        timezone: str = "UTC",
        idempotency_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Books an interview slot idempotently.
        """
        # Idempotency check
        if idempotency_key:
            for evt in self.booked_events:
                if evt.get("idempotency_key") == idempotency_key:
                    return {
                        "status": "already_booked",
                        "calendar_event_id": evt["calendar_event_id"],
                        "meeting_link": evt["meeting_link"],
                        "event": evt
                    }

        # Conflict check
        for evt in self.booked_events:
            if evt["interviewer_email"] == interviewer_email and evt["status"] == "scheduled":
                if max(start_time, evt["start_time"]) < min(end_time, evt["end_time"]):
                    raise ValueError(f"Scheduling conflict: Interviewer {interviewer_email} is already booked at that time.")

        event_id = f"gcal_{uuid.uuid4().hex[:10]}"
        meet_id = f"{uuid.uuid4().hex[:3]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:3]}"
        meeting_link = f"https://meet.google.com/{meet_id}"

        event_record = {
            "calendar_event_id": event_id,
            "candidate_email": candidate_email,
            "interviewer_email": interviewer_email,
            "start_time": start_time,
            "end_time": end_time,
            "timezone": timezone,
            "title": title,
            "meeting_link": meeting_link,
            "status": "scheduled",
            "idempotency_key": idempotency_key,
            "created_at": datetime.utcnow()
        }
        self.booked_events.append(event_record)
        return {
            "status": "scheduled",
            "calendar_event_id": event_id,
            "meeting_link": meeting_link,
            "event": event_record
        }

    def cancel_event(self, calendar_event_id: str) -> bool:
        for evt in self.booked_events:
            if evt["calendar_event_id"] == calendar_event_id:
                evt["status"] = "cancelled"
                return True
        return False

calendar_service = CalendarService()
