import asyncio
from pathlib import Path
from backend.database.session import SessionLocal, Base, engine
from backend.database.models import Job, Candidate, Resume
from backend.orchestrator.recruitment_graph import orchestrator
from backend.core.config import settings

SAMPLE_RESUME_1 = """
Alice Vance
Email: alice.vance@example.com
Phone: +1 415-555-0142

PROFESSIONAL SUMMARY
Senior Software Engineer with 4.5 years of experience architecting distributed backend services, high-throughput APIs, and machine learning pipelines.

TECHNICAL SKILLS
- Programming & Frameworks: Python, FastAPI, Django, SQL, PostgreSQL, Redis
- Infrastructure & Cloud: Docker, Kubernetes, AWS, Linux, CI/CD
- AI & Data: Machine Learning, PyTorch, Pandas, NumPy

EXPERIENCE
Lead Backend Engineer | CloudScale Inc. (2022 - Present)
- Architected asynchronous microservices handling 12,000 req/sec using FastAPI and Redis.
- Implemented automated database query optimizations on PostgreSQL reducing latency by 45%.

Software Engineer | NeuralWorks (2020 - 2022)
- Built Python-based data ingestion pipelines and ML model inference endpoints with Docker.

EDUCATION
B.S. in Computer Science | University of California, Berkeley (2020)

PROJECTS
- Distributed Task Orchestrator: High-resilience worker queue using Python and Redis pub/sub.
- Automated Fraud Detection Engine: Machine learning classifier with 96% precision.
"""

SAMPLE_RESUME_2 = """
Bob Jenkins
Email: bob.jenkins@techmail.io
Phone: +1 212-555-0188

SUMMARY
Software Developer with 2 years of experience specializing in web development, database management, and cloud APIs.

SKILLS
Python, Flask, JavaScript, React, MySQL, Docker, Git

EXPERIENCE
Junior Software Developer | WebCraft Studios (2022 - Present)
- Developed REST APIs in Python using Flask and MySQL.
- Containerized local development environments with Docker.

EDUCATION
B.Tech in Information Technology | City Institute of Technology (2022)

PROJECTS
- Inventory Management Dashboard: Full-stack React and Flask application.
"""

SAMPLE_RESUME_3 = """
Charlie Lin
Email: charlie.lin@example.com
Phone: +1 650-555-0199

PROFILE
Frontend and UI specialist exploring backend technologies.

SKILLS
JavaScript, TypeScript, React, HTML, CSS, TailwindCSS, Node.js

EXPERIENCE
Frontend Developer (2023 - Present)
- Developed responsive web interfaces.

EDUCATION
B.A. in Interactive Design (2023)
"""

async def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Clear existing data for clean demo
    print("Seeding database...")
    job = Job(
        title="Senior AI Platform Engineer",
        department="AI Systems & Infrastructure",
        description="We are seeking an experienced Senior AI Platform Engineer to build scalable backend services, orchestrate LLM workflows, and manage distributed data infrastructure.",
        required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        preferred_skills=["Machine Learning", "Kubernetes", "Redis"],
        min_experience_years=3,
        rubric={"skills_weight": 0.5, "experience_weight": 0.3, "projects_weight": 0.2},
        workflow_config={"auto_approve_threshold": 80.0, "require_recruiter_review": True}
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    print(f"Created Job: {job.title} (ID: {job.id})")

    resumes = [
        ("Alice Vance", "alice_vance_resume.txt", SAMPLE_RESUME_1),
        ("Bob Jenkins", "bob_jenkins_resume.txt", SAMPLE_RESUME_2),
        ("Charlie Lin", "charlie_lin_resume.txt", SAMPLE_RESUME_3)
    ]

    for name, filename, text in resumes:
        # Save resume file
        file_path = settings.UPLOAD_DIR / filename
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text.strip())

        candidate = Candidate(
            job_id=job.id,
            name=name,
            status="Applied"
        )
        db.add(candidate)
        db.flush()

        res_record = Resume(
            candidate_id=candidate.id,
            file_path=str(file_path),
            filename=filename,
            file_type="txt",
            raw_text=text.strip(),
            parsing_status="success"
        )
        db.add(res_record)
        orchestrator.record_event(
            db, candidate.id, job.id, None, "Applied", "system",
            "seed_resume_intake", {"filename": filename}
        )
        db.commit()

        # Run pipeline
        print(f"Running multi-agent pipeline for {name}...")
        await orchestrator.run_screening_pipeline(db, candidate.id)

    print("Seeding completed successfully! Open http://localhost:8000 to view recruiter dashboard.")
    db.close()

if __name__ == "__main__":
    asyncio.run(seed())
