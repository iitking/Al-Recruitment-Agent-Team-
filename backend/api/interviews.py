from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import Interview, Candidate
from backend.schemas.interview import (
    SlotSuggestionRequest, SlotSuggestionResponse, InterviewSlot,
    InterviewCreateRequest, InterviewResponse, InterviewUpdateRequest
)
from backend.agents.scheduling_agent import scheduling_agent
from backend.orchestrator.recruitment_graph import orchestrator

router = APIRouter(prefix="/interviews", tags=["Interviews & Scheduling"])

@router.post("/suggest-slots", response_model=SlotSuggestionResponse)
def suggest_interview_slots(
    req: SlotSuggestionRequest,
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    raw_slots = scheduling_agent.suggest_slots(
        interviewer_email=req.interviewer_email or "interviewer@company.com",
        duration_minutes=req.duration_minutes,
        days_ahead=req.days_ahead
    )

    slot_objects = [InterviewSlot(**s) for s in raw_slots]
    return SlotSuggestionResponse(
        candidate_id=candidate.id,
        interviewer_email=req.interviewer_email or "interviewer@company.com",
        suggested_slots=slot_objects
    )

@router.post("", response_model=InterviewResponse)
def create_interview_booking(
    req: InterviewCreateRequest,
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == req.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    try:
        booking = scheduling_agent.schedule_interview(
            candidate_email=candidate.email or "candidate@example.com",
            interviewer_email=req.interviewer_email,
            start_time=req.start_time,
            end_time=req.end_time,
            title=req.title or "Technical Interview",
            timezone=req.timezone or "UTC",
            idempotency_key=req.idempotency_key
        )
    except ValueError as ve:
        raise HTTPException(status_code=409, detail=str(ve))

    # Persist interview record
    interview = Interview(
        candidate_id=candidate.id,
        interviewer_email=req.interviewer_email,
        candidate_email=candidate.email or "candidate@example.com",
        start_time=req.start_time,
        end_time=req.end_time,
        timezone=req.timezone or "UTC",
        title=req.title or "Technical Interview",
        meeting_link=booking["meeting_link"],
        calendar_event_id=booking["calendar_event_id"],
        status="scheduled",
        idempotency_key=req.idempotency_key,
        notes=req.notes
    )
    db.add(interview)

    # Transition state to Scheduled
    prev_status = candidate.status
    candidate.status = "Scheduled"
    orchestrator.record_event(
        db, candidate.id, candidate.job_id, prev_status, "Scheduled",
        "scheduling_agent", "interview_scheduled", {
            "calendar_event_id": booking["calendar_event_id"],
            "meeting_link": booking["meeting_link"],
            "start_time": req.start_time.isoformat()
        }
    )
    db.commit()
    db.refresh(interview)
    return interview

@router.patch("/{interview_id}", response_model=InterviewResponse)
def update_interview(
    interview_id: str,
    req: InterviewUpdateRequest,
    db: Session = Depends(get_db)
):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    candidate = db.query(Candidate).filter(Candidate.id == interview.candidate_id).first()

    if req.start_time:
        interview.start_time = req.start_time
    if req.end_time:
        interview.end_time = req.end_time
    if req.notes is not None:
        interview.notes = req.notes
    if req.status:
        interview.status = req.status
        if req.status.lower() == "completed" and candidate:
            candidate.status = "InterviewCompleted"
            orchestrator.record_event(
                db, candidate.id, candidate.job_id, "Scheduled", "InterviewCompleted",
                "recruiter", "interview_completed", {"interview_id": interview.id}
            )
        elif req.status.lower() == "cancelled":
            scheduling_agent.cancel_interview(interview.calendar_event_id or "")

    db.commit()
    db.refresh(interview)
    return interview

@router.get("", response_model=List[InterviewResponse])
def list_interviews(
    candidate_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Interview)
    if candidate_id:
        query = query.filter(Interview.candidate_id == candidate_id)
    if status:
        query = query.filter(Interview.status == status)
    return query.order_by(Interview.start_time.asc()).all()
