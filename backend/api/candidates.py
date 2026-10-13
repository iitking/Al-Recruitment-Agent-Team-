from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import Candidate, MatchingReport
from backend.schemas.candidate import CandidateResponse
from backend.schemas.screening import MatchingReportResponse
from backend.schemas.interview import CandidateAvailabilityRequest
from backend.orchestrator.recruitment_graph import orchestrator

router = APIRouter(prefix="/candidates", tags=["Candidates"])

@router.get("", response_model=List[CandidateResponse])
def list_candidates(
    job_id: Optional[str] = Query(None, description="Filter by Job ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db)
):
    query = db.query(Candidate)
    if job_id:
        query = query.filter(Candidate.job_id == job_id)
    if status:
        query = query.filter(Candidate.status == status)

    candidates = query.order_by(Candidate.created_at.desc()).all()
    
    # Enrich with latest score
    result = []
    for c in candidates:
        c_resp = CandidateResponse.from_orm(c)
        latest_rep = db.query(MatchingReport).filter(MatchingReport.candidate_id == c.id).order_by(MatchingReport.created_at.desc()).first()
        if latest_rep:
            c_resp.latest_score = latest_rep.match_score
            c_resp.latest_recommendation = latest_rep.recommendation
        result.append(c_resp)

    return result

@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    c_resp = CandidateResponse.from_orm(candidate)
    latest_rep = db.query(MatchingReport).filter(MatchingReport.candidate_id == candidate.id).order_by(MatchingReport.created_at.desc()).first()
    if latest_rep:
        c_resp.latest_score = latest_rep.match_score
        c_resp.latest_recommendation = latest_rep.recommendation
    return c_resp

@router.get("/{candidate_id}/report", response_model=MatchingReportResponse)
def get_screening_report(candidate_id: str, db: Session = Depends(get_db)):
    report = db.query(MatchingReport).filter(MatchingReport.candidate_id == candidate_id).order_by(MatchingReport.created_at.desc()).first()
    if not report:
        raise HTTPException(status_code=404, detail="Screening report not found for candidate")
    return report

@router.post("/{candidate_id}/reprocess")
async def reprocess_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """
    Reruns the parsing and screening agent pipeline for this candidate.
    """
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    result = await orchestrator.run_screening_pipeline(db, candidate_id)
    return {"message": "Candidate reprocessed successfully", "result": result}

@router.post("/{candidate_id}/availability")
def record_candidate_availability(
    candidate_id: str,
    avail: CandidateAvailabilityRequest,
    db: Session = Depends(get_db)
):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    orchestrator.record_event(
        db, candidate_id, candidate.job_id, candidate.status, "AwaitingAvailability",
        "candidate", "availability_submitted", avail.dict()
    )
    db.commit()
    return {"status": "success", "message": "Availability recorded successfully"}
