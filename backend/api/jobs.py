import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.database.models import Job, Candidate, Resume
from backend.schemas.job import JobCreate, JobResponse
from backend.schemas.candidate import CandidateResponse
from backend.core.config import settings
from backend.services.resume_service import ResumeService
from backend.orchestrator.recruitment_graph import orchestrator

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("", response_model=JobResponse)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    job = Job(
        title=job_in.title,
        department=job_in.department,
        description=job_in.description,
        required_skills=job_in.required_skills,
        preferred_skills=job_in.preferred_skills,
        min_experience_years=job_in.min_experience_years,
        rubric=job_in.rubric,
        workflow_config=job_in.workflow_config
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).order_by(Job.created_at.desc()).all()
    # compute candidate counts
    res = []
    for j in jobs:
        cnt = db.query(Candidate).filter(Candidate.job_id == j.id).count()
        j_dict = JobResponse.from_orm(j)
        j_dict.candidate_count = cnt
        res.append(j_dict)
    return res

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    cnt = db.query(Candidate).filter(Candidate.job_id == job.id).count()
    resp = JobResponse.from_orm(job)
    resp.candidate_count = cnt
    return resp

@router.post("/{job_id}/resumes", response_model=List[CandidateResponse])
async def upload_resumes(
    job_id: str,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    created_candidates = []

    for file in files:
        filename = file.filename or "resume.pdf"
        file_ext = filename.split(".")[-1].lower() if "." in filename else "pdf"

        # Read content
        content = await file.read()
        file_hash = ResumeService.compute_sha256(content)

        # Store to disk securely
        safe_filename = f"{job_id}_{file_hash[:8]}_{Path(filename).name}"
        dest_path = settings.UPLOAD_DIR / safe_filename
        with open(dest_path, "wb") as buffer:
            buffer.write(content)

        # Create Candidate record
        candidate = Candidate(
            job_id=job.id,
            name="New Applicant",
            status="Applied"
        )
        db.add(candidate)
        db.flush()

        # Create Resume record
        resume = Resume(
            candidate_id=candidate.id,
            file_path=str(dest_path),
            filename=filename,
            file_type=file_ext,
            file_hash=file_hash,
            parsing_status="pending"
        )
        db.add(resume)
        orchestrator.record_event(
            db, candidate.id, job.id, None, "Applied", "system",
            "resume_uploaded", {"filename": filename, "file_hash": file_hash}
        )
        db.commit()
        db.refresh(candidate)

        # Run automated multi-agent screening pipeline
        try:
            await orchestrator.run_screening_pipeline(db, candidate.id)
            db.refresh(candidate)
        except Exception as e:
            orchestrator.record_event(
                db, candidate.id, job.id, "Applied", "NeedsManualReview", "system",
                "pipeline_execution_error", {"error": str(e)}
            )
            candidate.status = "NeedsManualReview"
            db.commit()

        created_candidates.append(candidate)

    return created_candidates
