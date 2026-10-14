from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.session import get_db
from backend.database.models import Job, Candidate, MatchingReport, Interview, WorkflowEvent, CandidateProfile
from backend.schemas.dashboard import DashboardSummaryResponse, WorkflowEventResponse

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    total_jobs = db.query(Job).count()
    active_jobs = db.query(Job).filter(Job.is_active == True).count()
    total_candidates = db.query(Candidate).count()

    # Candidates by status
    candidates = db.query(Candidate.status).all()
    status_counts = dict(Counter([c[0] for c in candidates if c[0]]))

    # Average score
    avg_score_query = db.query(func.avg(MatchingReport.match_score)).scalar()
    avg_score = round(float(avg_score_query), 1) if avg_score_query is not None else None

    # Flagged candidates count (NeedsManualReview or profiles with warnings)
    flagged_count = db.query(Candidate).filter(
        (Candidate.status == "NeedsManualReview")
    ).count()

    # Scheduled interviews count
    scheduled_interviews = db.query(Interview).filter(Interview.status == "scheduled").count()

    # Recent events
    recent_events_db = db.query(WorkflowEvent).order_by(WorkflowEvent.timestamp.desc()).limit(15).all()
    recent_events = [WorkflowEventResponse.from_orm(e) for e in recent_events_db]

    return DashboardSummaryResponse(
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        total_candidates=total_candidates,
        candidates_by_status=status_counts,
        avg_screening_score=avg_score,
        flagged_candidates_count=flagged_count,
        scheduled_interviews_count=scheduled_interviews,
        recent_events=recent_events
    )
