import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.database.models import (
    Candidate, Resume, CandidateProfile, MatchingReport, WorkflowEvent, Job
)
from backend.services.resume_service import ResumeService
from backend.agents.resume_parser import resume_parser_agent
from backend.agents.job_matcher import job_matcher_agent
from backend.agents.screening_agent import screening_agent
from backend.agents.communication_agent import communication_agent
from backend.agents.scheduling_agent import scheduling_agent

logger = logging.getLogger("orchestrator")

class RecruitmentOrchestrator:
    """
    State machine and multi-agent orchestrator managing the end-to-end recruitment pipeline.
    Ensures safe checkpoints, state persistence, audit history, and human-in-the-loop review.
    """

    def record_event(
        self,
        db: Session,
        candidate_id: str,
        job_id: Optional[str],
        previous_status: Optional[str],
        new_status: str,
        actor_type: str,
        event_type: str,
        details: Optional[Dict[str, Any]] = None
    ) -> WorkflowEvent:
        event = WorkflowEvent(
            candidate_id=candidate_id,
            job_id=job_id,
            previous_status=previous_status,
            new_status=new_status,
            actor_type=actor_type,
            event_type=event_type,
            details=details or {},
            timestamp=datetime.utcnow()
        )
        db.add(event)
        return event

    async def run_screening_pipeline(
        self,
        db: Session,
        candidate_id: str
    ) -> Dict[str, Any]:
        """
        Executes the screening pipeline:
        Resume Parsing -> Job Matching -> Evaluation -> Recruiter Review Queue
        """
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found.")

        job = db.query(Job).filter(Job.id == candidate.job_id).first()
        if not job:
            raise ValueError(f"Job {candidate.job_id} not found.")

        resume = db.query(Resume).filter(Resume.candidate_id == candidate_id).first()
        if not resume:
            raise ValueError(f"Resume for candidate {candidate_id} not found.")

        # --- STEP 1: PARSING AGENT ---
        prev_status = candidate.status
        candidate.status = "Parsing"
        self.record_event(db, candidate_id, job.id, prev_status, "Parsing", "orchestrator", "started_parsing")
        db.commit()

        # Extract text if not already populated
        if not resume.raw_text:
            extracted_text, err = ResumeService.extract_text(resume.file_path, resume.file_type)
            if err:
                resume.parsing_status = "failed"
                candidate.status = "NeedsManualReview"
                self.record_event(
                    db, candidate_id, job.id, "Parsing", "NeedsManualReview", "resume_parser",
                    "parsing_failed", {"error": err}
                )
                db.commit()
                return {"status": "NeedsManualReview", "error": err}
            resume.raw_text = extracted_text
            resume.parsing_status = "success"

        # Agent parses into structured profile
        parsed_data = await resume_parser_agent.parse(resume.raw_text)
        profile_obj = parsed_data["profile"]

        # Update candidate contact info if discovered in resume
        if parsed_data.get("name") and candidate.name in [None, "", "Unknown Candidate"]:
            candidate.name = parsed_data["name"]
        if parsed_data.get("email") and not candidate.email:
            candidate.email = parsed_data["email"]
        if parsed_data.get("phone") and not candidate.phone:
            candidate.phone = parsed_data["phone"]

        # Persist CandidateProfile
        existing_profile = db.query(CandidateProfile).filter(CandidateProfile.candidate_id == candidate_id).first()
        if existing_profile:
            existing_profile.skills = profile_obj.skills
            existing_profile.experience_years = profile_obj.experience_years
            existing_profile.education = profile_obj.education
            existing_profile.certifications = profile_obj.certifications
            existing_profile.employment_history = profile_obj.employment_history
            existing_profile.projects = profile_obj.projects
            existing_profile.extraction_warnings = profile_obj.extraction_warnings
            existing_profile.needs_manual_review = profile_obj.needs_manual_review
        else:
            db_profile = CandidateProfile(
                candidate_id=candidate_id,
                skills=profile_obj.skills,
                experience_years=profile_obj.experience_years,
                education=profile_obj.education,
                certifications=profile_obj.certifications,
                employment_history=profile_obj.employment_history,
                projects=profile_obj.projects,
                extraction_warnings=profile_obj.extraction_warnings,
                needs_manual_review=profile_obj.needs_manual_review
            )
            db.add(db_profile)

        db.commit()

        if profile_obj.needs_manual_review:
            candidate.status = "NeedsManualReview"
            self.record_event(
                db, candidate_id, job.id, "Parsing", "NeedsManualReview", "resume_parser",
                "manual_review_flagged", {"warnings": profile_obj.extraction_warnings}
            )
            db.commit()
            return {"status": "NeedsManualReview", "warnings": profile_obj.extraction_warnings}

        # --- STEP 2: JOB MATCHING AGENT ---
        candidate.status = "Matching"
        self.record_event(db, candidate_id, job.id, "Parsing", "Matching", "orchestrator", "started_matching")
        db.commit()

        job_reqs = {
            "required_skills": job.required_skills or [],
            "preferred_skills": job.preferred_skills or [],
            "min_experience_years": job.min_experience_years or 0,
            "rubric": job.rubric or {}
        }

        matching_result = await job_matcher_agent.match(
            candidate_profile=profile_obj.model_dump(),
            raw_text=resume.raw_text,
            job_requirements=job_reqs
        )

        # --- STEP 3: SCREENING & EVALUATION AGENT ---
        candidate.status = "Evaluation"
        self.record_event(db, candidate_id, job.id, "Matching", "Evaluation", "orchestrator", "started_evaluation")
        db.commit()

        evaluation_result = screening_agent.evaluate(
            candidate_profile=profile_obj.model_dump(),
            matching_result=matching_result,
            job_requirements=job_reqs
        )

        # Persist MatchingReport
        matched_dicts = [m.model_dump() if hasattr(m, "model_dump") else m for m in matching_result["matched_requirements"]]
        existing_rep = db.query(MatchingReport).filter(MatchingReport.candidate_id == candidate_id).first()
        if existing_rep:
            existing_rep.matched_requirements = matched_dicts
            existing_rep.missing_or_unclear_requirements = matching_result["missing_or_unclear_requirements"]
            existing_rep.match_score = evaluation_result["match_score"]
            existing_rep.rubric_breakdown = evaluation_result["rubric_breakdown"]
            existing_rep.recommendation = evaluation_result["recommendation"]
            existing_rep.recommendation_rationale = evaluation_result["recommendation_rationale"]
            existing_rep.review_flags = evaluation_result["review_flags"]
        else:
            rep = MatchingReport(
                candidate_id=candidate_id,
                job_id=job.id,
                matched_requirements=matched_dicts,
                missing_or_unclear_requirements=matching_result["missing_or_unclear_requirements"],
                match_score=evaluation_result["match_score"],
                rubric_breakdown=evaluation_result["rubric_breakdown"],
                recommendation=evaluation_result["recommendation"],
                recommendation_rationale=evaluation_result["recommendation_rationale"],
                review_flags=evaluation_result["review_flags"]
            )
            db.add(rep)

        # --- STEP 4: ROUTE TO RECRUITER REVIEW ---
        candidate.status = "RecruiterReview"
        self.record_event(
            db, candidate_id, job.id, "Evaluation", "RecruiterReview", "orchestrator",
            "ready_for_recruiter_review", {
                "score": evaluation_result["match_score"],
                "recommendation": evaluation_result["recommendation"]
            }
        )
        db.commit()

        return {
            "status": "RecruiterReview",
            "candidate_id": candidate_id,
            "match_score": evaluation_result["match_score"],
            "recommendation": evaluation_result["recommendation"]
        }

    def process_recruiter_decision(
        self,
        db: Session,
        candidate_id: str,
        decision: str,
        recruiter_name: str = "Recruiter",
        notes: str = "",
        override: bool = False
    ) -> Dict[str, Any]:
        """
        Handles recruiter human-in-the-loop decision:
        - approved -> ApprovedForInterview -> drafts interview invitation -> AwaitingAvailability
        - clarification_requested -> Clarification -> drafts clarification request
        - on_hold -> OnHold
        - rejected -> Rejected
        """
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise ValueError(f"Candidate {candidate_id} not found.")

        job = db.query(Job).filter(Job.id == candidate.job_id).first()
        prev_status = candidate.status

        decision_clean = decision.lower().strip()
        new_status = "RecruiterReview"

        if decision_clean in ("approved", "approve"):
            new_status = "ApprovedForInterview"
        elif decision_clean in ("clarification_requested", "clarification", "clarify"):
            new_status = "Clarification"
        elif decision_clean in ("on_hold", "hold"):
            new_status = "OnHold"
        elif decision_clean in ("rejected", "reject"):
            new_status = "Rejected"
        else:
            raise ValueError(f"Unknown recruiter decision '{decision}'")

        candidate.status = new_status
        self.record_event(
            db, candidate_id, candidate.job_id, prev_status, new_status, "recruiter",
            f"recruiter_action_{decision_clean}", {
                "recruiter": recruiter_name,
                "notes": notes,
                "override": override
            }
        )
        db.commit()

        # If approved, draft interview invitation email automatically
        if new_status == "ApprovedForInterview":
            draft = communication_agent.draft_communication(
                candidate_name=candidate.name or "Candidate",
                recipient_email=candidate.email or "candidate@example.com",
                job_title=job.title if job else "Role",
                template_type="interview_invitation"
            )
            candidate.status = "AwaitingAvailability"
            self.record_event(
                db, candidate_id, candidate.job_id, "ApprovedForInterview", "AwaitingAvailability",
                "communication_agent", "drafted_interview_invitation", {"draft_subject": draft["subject"]}
            )
            db.commit()

        elif new_status == "Clarification":
            draft = communication_agent.draft_communication(
                candidate_name=candidate.name or "Candidate",
                recipient_email=candidate.email or "candidate@example.com",
                job_title=job.title if job else "Role",
                template_type="clarification",
                extra_vars={"missing_items": notes or "project details"}
            )
            self.record_event(
                db, candidate_id, candidate.job_id, "Clarification", "Clarification",
                "communication_agent", "drafted_clarification_email", {"draft_subject": draft["subject"]}
            )
            db.commit()

        return {
            "candidate_id": candidate_id,
            "decision": decision_clean,
            "new_status": candidate.status,
            "recruiter_name": recruiter_name
        }

orchestrator = RecruitmentOrchestrator()
