import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.session import Base
from backend.database.models import Job, Candidate, Resume
from backend.orchestrator.recruitment_graph import orchestrator
from backend.services.email_service import email_service
from backend.services.calendar_service import calendar_service

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

@pytest.mark.asyncio
async def test_recruitment_orchestrator_flow(test_db):
    # 1. Create Job
    job = Job(
        title="Senior AI Engineer",
        description="Looking for an engineer skilled in Python and Machine Learning",
        required_skills=["Python", "FastAPI"],
        preferred_skills=["Docker"],
        min_experience_years=2
    )
    test_db.add(job)
    test_db.commit()

    # 2. Create Candidate & Resume
    candidate = Candidate(job_id=job.id, name="Test Applicant", status="Applied")
    test_db.add(candidate)
    test_db.commit()

    resume = Resume(
        candidate_id=candidate.id,
        file_path="mock.pdf",
        filename="test_resume.pdf",
        file_type="txt",
        raw_text="Jane Doe\nEmail: jane@example.com\nSkills: Python, FastAPI, Docker\nExperience: 3 years\nProjects: AI Assistant"
    )
    test_db.add(resume)
    test_db.commit()

    # 3. Run screening pipeline
    result = await orchestrator.run_screening_pipeline(test_db, candidate.id)
    assert result["status"] == "RecruiterReview"
    assert candidate.status == "RecruiterReview"
    assert candidate.email == "jane@example.com"

    # 4. Recruiter reviews and approves
    review_res = orchestrator.process_recruiter_decision(
        db=test_db,
        candidate_id=candidate.id,
        decision="approved",
        recruiter_name="Lead Recruiter",
        notes="Strong alignment on Python."
    )
    assert review_res["new_status"] == "AwaitingAvailability"

    # 5. Scheduling agent books interview
    start = datetime.utcnow() + timedelta(days=2, hours=10)
    end = start + timedelta(minutes=45)
    booking = calendar_service.create_event(
        candidate_email=candidate.email,
        interviewer_email="lead@company.com",
        start_time=start,
        end_time=end,
        idempotency_key="unique_booking_001"
    )
    assert booking["status"] == "scheduled"
    assert "meet.google.com" in booking["meeting_link"]

    # 6. Idempotency test
    duplicate_booking = calendar_service.create_event(
        candidate_email=candidate.email,
        interviewer_email="lead@company.com",
        start_time=start,
        end_time=end,
        idempotency_key="unique_booking_001"
    )
    assert duplicate_booking["status"] == "already_booked"
