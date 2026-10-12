import pytest
from backend.agents.job_matcher import job_matcher_agent
from backend.agents.screening_agent import screening_agent

@pytest.mark.asyncio
async def test_job_matcher_and_screening():
    candidate_profile = {
        "skills": ["python", "fastapi", "docker", "sql"],
        "experience_years": 4.0,
        "projects": ["Fraud Detection Pipeline", "Distributed Task Scheduler"]
    }
    raw_text = "Proficient in Python and FastAPI backend development. 4 years of experience."
    job_reqs = {
        "required_skills": ["Python", "FastAPI"],
        "preferred_skills": ["Docker", "Kubernetes"],
        "min_experience_years": 3,
        "rubric": {
            "skills_weight": 0.5,
            "experience_weight": 0.3,
            "projects_weight": 0.2
        }
    }

    match_res = await job_matcher_agent.match(candidate_profile, raw_text, job_reqs)
    matched_req_names = [m.requirement for m in match_res["matched_requirements"]]

    assert any("Python" in r for r in matched_req_names)
    assert any("FastAPI" in r for r in matched_req_names)
    assert any("Kubernetes" in r for r in match_res["missing_or_unclear_requirements"])

    eval_res = screening_agent.evaluate(candidate_profile, match_res, job_reqs)
    assert eval_res["match_score"] >= 70.0
    assert eval_res["recommendation"] in ["Strong Match", "Potential Match"]
    assert "skills_score" in eval_res["rubric_breakdown"]
