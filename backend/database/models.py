import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from backend.database.session import Base

def generate_uuid(prefix: str = "") -> str:
    return f"{prefix}{uuid.uuid4().hex[:12]}"

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("job_"))
    title = Column(String(255), nullable=False)
    department = Column(String(128), nullable=True)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)        # list of strings
    preferred_skills = Column(JSON, default=list)       # list of strings
    min_experience_years = Column(Integer, default=0)
    rubric = Column(JSON, default=dict)                 # e.g. {"skills_weight": 0.5, "experience_weight": 0.3, "projects_weight": 0.2}
    workflow_config = Column(JSON, default=dict)        # auto_approve_threshold, require_recruiter_review
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    candidates = relationship("Candidate", back_populates="job", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("cand_"))
    job_id = Column(String(64), ForeignKey("jobs.id"), nullable=False)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(64), nullable=True)
    status = Column(String(64), default="Applied")
    # Statuses: Applied, Parsing, NeedsManualReview, Parsed, Matching, Evaluation, 
    # RecruiterReview, Clarification, OnHold, ApprovedForInterview, AwaitingAvailability, 
    # Scheduling, Scheduled, InterviewCompleted, Rejected, Withdrawn
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="candidates")
    resume = relationship("Resume", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    profile = relationship("CandidateProfile", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    matching_reports = relationship("MatchingReport", back_populates="candidate", cascade="all, delete-orphan")
    review_decisions = relationship("ReviewDecision", back_populates="candidate", cascade="all, delete-orphan")
    communications = relationship("Communication", back_populates="candidate", cascade="all, delete-orphan")
    interviews = relationship("Interview", back_populates="candidate", cascade="all, delete-orphan")
    events = relationship("WorkflowEvent", back_populates="candidate", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("res_"))
    candidate_id = Column(String(64), ForeignKey("candidates.id"), nullable=False, unique=True)
    file_path = Column(String(512), nullable=False)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)      # pdf, docx, txt
    file_hash = Column(String(64), nullable=True)
    raw_text = Column(Text, nullable=True)
    parsing_status = Column(String(32), default="pending") # pending, success, failed, flagged
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="resume")


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("prof_"))
    candidate_id = Column(String(64), ForeignKey("candidates.id"), nullable=False, unique=True)
    skills = Column(JSON, default=list)
    experience_years = Column(Float, default=0.0)
    education = Column(JSON, default=list)              # list of degrees / institutions
    certifications = Column(JSON, default=list)
    employment_history = Column(JSON, default=list)     # list of roles, companies, summaries
    projects = Column(JSON, default=list)
    extraction_warnings = Column(JSON, default=list)
    needs_manual_review = Column(Boolean, default=False)
    parsed_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="profile")


class MatchingReport(Base):
    __tablename__ = "matching_reports"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("rep_"))
    candidate_id = Column(String(64), ForeignKey("candidates.id"), nullable=False)
    job_id = Column(String(64), ForeignKey("jobs.id"), nullable=False)
    matched_requirements = Column(JSON, default=list)   # [{"requirement": "...", "evidence": "..."}]
    missing_or_unclear_requirements = Column(JSON, default=list)
    match_score = Column(Float, nullable=True)          # e.g. 85.5
    rubric_breakdown = Column(JSON, default=dict)       # {"skills_score": 90, "experience_score": 80, ...}
    recommendation = Column(String(64), nullable=True)  # Strong Match, Potential Match, Needs Clarification, Low Match
    recommendation_rationale = Column(Text, nullable=True)
    review_flags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="matching_reports")


class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("rev_"))
    candidate_id = Column(String(64), ForeignKey("candidates.id"), nullable=False)
    recruiter_name = Column(String(128), default="Recruiter")
    decision = Column(String(64), nullable=False)       # approved, rejected, clarification_requested, on_hold
    notes = Column(Text, nullable=True)
    overridden = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="review_decisions")


class Communication(Base):
    __tablename__ = "communications"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("comm_"))
    candidate_id = Column(String(64), ForeignKey("candidates.id"), nullable=False)
    template_type = Column(String(64), nullable=False)  # interview_invitation, clarification, status_update, rejection
    recipient_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    status = Column(String(32), default="draft")        # draft, approved, sent, failed
    idempotency_key = Column(String(128), nullable=True, unique=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="communications")


class Interview(Base):
    __tablename__ = "interviews"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("int_"))
    candidate_id = Column(String(64), ForeignKey("candidates.id"), nullable=False)
    interviewer_email = Column(String(255), nullable=False)
    candidate_email = Column(String(255), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    timezone = Column(String(64), default="UTC")
    title = Column(String(255), default="Candidate Interview")
    meeting_link = Column(String(512), nullable=True)
    calendar_event_id = Column(String(128), nullable=True)
    status = Column(String(32), default="scheduled")    # proposed, scheduled, completed, cancelled, rescheduled
    idempotency_key = Column(String(128), nullable=True, unique=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="interviews")


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("evt_"))
    candidate_id = Column(String(64), ForeignKey("candidates.id"), nullable=False)
    job_id = Column(String(64), nullable=True)
    previous_status = Column(String(64), nullable=True)
    new_status = Column(String(64), nullable=False)
    actor_type = Column(String(32), default="system")   # system, agent, recruiter
    event_type = Column(String(64), nullable=False)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="events")


class IntegrationToken(Base):
    __tablename__ = "integration_tokens"

    id = Column(String(64), primary_key=True, default=lambda: generate_uuid("tok_"))
    provider = Column(String(64), nullable=False)       # google_calendar, microsoft_graph, smtp
    token_data = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
