from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import Candidate, Job, Communication, ReviewDecision
from backend.schemas.screening import RecruiterReviewRequest, RecruiterReviewResponse
from backend.schemas.communication import (
    CommunicationDraftRequest, CommunicationSendRequest, CommunicationResponse
)
from backend.orchestrator.recruitment_graph import orchestrator
from backend.agents.communication_agent import communication_agent

router = APIRouter(tags=["Screening & Review"])

@router.post("/candidates/{candidate_id}/review", response_model=RecruiterReviewResponse)
def submit_recruiter_review(
    candidate_id: str,
    req: RecruiterReviewRequest,
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Record decision in table
    decision_rec = ReviewDecision(
        candidate_id=candidate_id,
        recruiter_name=req.recruiter_name or "Recruiter",
        decision=req.decision,
        notes=req.notes,
        overridden=req.override or False
    )
    db.add(decision_rec)
    db.commit()

    # Transition state in orchestrator
    res = orchestrator.process_recruiter_decision(
        db=db,
        candidate_id=candidate_id,
        decision=req.decision,
        recruiter_name=req.recruiter_name or "Recruiter",
        notes=req.notes or "",
        override=req.override or False
    )

    return RecruiterReviewResponse(
        id=decision_rec.id,
        candidate_id=candidate_id,
        decision=req.decision,
        recruiter_name=req.recruiter_name or "Recruiter",
        notes=req.notes,
        overridden=req.override or False,
        new_candidate_status=res["new_status"],
        created_at=decision_rec.created_at
    )

@router.post("/candidates/{candidate_id}/communications/draft", response_model=CommunicationResponse)
def draft_candidate_communication(
    candidate_id: str,
    req: CommunicationDraftRequest,
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    job = db.query(Job).filter(Job.id == candidate.job_id).first()

    draft = communication_agent.draft_communication(
        candidate_name=candidate.name or "Candidate",
        recipient_email=candidate.email or "candidate@example.com",
        job_title=job.title if job else "Open Position",
        template_type=req.template_type,
        extra_vars={"notes": req.custom_instructions or ""}
    )

    comm = Communication(
        candidate_id=candidate_id,
        template_type=draft["template_type"],
        recipient_email=draft["recipient_email"],
        subject=draft["subject"],
        body=draft["body"],
        status="draft",
        idempotency_key=draft["idempotency_key"]
    )
    db.add(comm)
    db.commit()
    db.refresh(comm)
    return comm

@router.post("/candidates/{candidate_id}/communications/send", response_model=CommunicationResponse)
def send_candidate_communication(
    candidate_id: str,
    req: CommunicationSendRequest,
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Look for most recent draft or create from request
    comm = db.query(Communication).filter(
        Communication.candidate_id == candidate_id,
        Communication.status == "draft"
    ).order_by(Communication.created_at.desc()).first()

    subject = req.subject or (comm.subject if comm else f"Update on your application")
    body = req.body or (comm.body if comm else f"Dear {candidate.name}, here is an update.")
    idempotency_key = req.idempotency_key or (comm.idempotency_key if comm else None)

    send_res = communication_agent.send_communication(
        recipient_email=candidate.email or "candidate@example.com",
        subject=subject,
        body=body,
        idempotency_key=idempotency_key
    )

    if not comm:
        comm = Communication(
            candidate_id=candidate_id,
            template_type="custom",
            recipient_email=candidate.email or "candidate@example.com",
            subject=subject,
            body=body,
            status="sent",
            idempotency_key=idempotency_key,
            sent_at=datetime.utcnow()
        )
        db.add(comm)
    else:
        comm.subject = subject
        comm.body = body
        comm.status = "sent"
        comm.sent_at = datetime.utcnow()

    orchestrator.record_event(
        db, candidate_id, candidate.job_id, candidate.status, candidate.status,
        "communication_agent", "communication_sent", {
            "delivered_via": send_res.get("delivered_via"),
            "subject": subject
        }
    )
    db.commit()
    db.refresh(comm)
    return comm

@router.get("/candidates/{candidate_id}/communications", response_model=List[CommunicationResponse])
def get_candidate_communications(candidate_id: str, db: Session = Depends(get_db)):
    return db.query(Communication).filter(Communication.candidate_id == candidate_id).order_by(Communication.created_at.desc()).all()
