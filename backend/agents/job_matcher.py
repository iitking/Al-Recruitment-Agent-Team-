import re
import json
from typing import Dict, Any, List
from backend.services.llm_service import llm_service
from backend.schemas.screening import RequirementEvidence
from backend.prompts import JOB_MATCHER_SYSTEM_PROMPT, JOB_MATCHER_USER_PROMPT

class JobMatcherAgent:
    """
    Compares candidate profile and resume text against job requirements.
    Extracts explicit textual evidence snippets for each requirement.
    """

    async def match(
        self,
        candidate_profile: Dict[str, Any],
        raw_text: str,
        job_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        required_skills: List[str] = job_requirements.get("required_skills", [])
        preferred_skills: List[str] = job_requirements.get("preferred_skills", [])
        min_experience_years: float = float(job_requirements.get("min_experience_years", 0))

        candidate_skills = [s.lower() for s in candidate_profile.get("skills", [])]
        candidate_exp = float(candidate_profile.get("experience_years", 0.0))

        # Try LLM-assisted matching if API key available
        if llm_service.api_key:
            llm_prompt = JOB_MATCHER_USER_PROMPT.format(
                job_title=job_requirements.get("title", "Open Role"),
                required_skills=required_skills,
                preferred_skills=preferred_skills,
                min_experience_years=min_experience_years,
                candidate_profile_json=json.dumps(candidate_profile),
                resume_excerpt=raw_text[:3000]
            )
            llm_result = await llm_service.generate_json(
                system_prompt=JOB_MATCHER_SYSTEM_PROMPT,
                user_prompt=llm_prompt
            )
            if llm_result and "matched_requirements" in llm_result:
                matched_items = [
                    RequirementEvidence(**item) if isinstance(item, dict) else RequirementEvidence(requirement=str(item), evidence="Found")
                    for item in llm_result.get("matched_requirements", [])
                ]
                return {
                    "matched_requirements": matched_items,
                    "missing_or_unclear_requirements": llm_result.get("missing_or_unclear_requirements", []),
                    "review_flags": llm_result.get("review_flags", [])
                }

        # Deterministic Evidence-based matching
        matched_requirements: List[RequirementEvidence] = []
        missing_or_unclear: List[str] = []
        review_flags: List[str] = []

        all_reqs = [(req, True) for req in required_skills] + [(req, False) for req in preferred_skills]

        for req, is_mandatory in all_reqs:
            req_lower = req.lower()
            evidence_snippet = None

            # 1. Check in parsed skills
            if req_lower in candidate_skills:
                evidence_snippet = f"Explicitly listed in candidate's skills inventory: '{req}'."
            else:
                # 2. Check in raw resume text for snippet
                pattern = r'([^.\n]*?' + re.escape(req_lower) + r'[^.\n]*)'
                text_match = re.search(pattern, raw_text, re.IGNORECASE)
                if text_match:
                    snippet = text_match.group(0).strip()
                    evidence_snippet = f"Found in resume text context: \"{snippet[:140]}\""

            if evidence_snippet:
                matched_requirements.append(
                    RequirementEvidence(
                        requirement=f"{req} ({'Required' if is_mandatory else 'Preferred'})",
                        evidence=evidence_snippet,
                        confidence=1.0,
                        matched=True
                    )
                )
            else:
                tag = f"{req} ({'Required' if is_mandatory else 'Preferred'})"
                missing_or_unclear.append(tag)
                if is_mandatory:
                    review_flags.append(f"Missing required qualification: {req}")

        # Check Experience Requirement
        if min_experience_years > 0:
            if candidate_exp >= min_experience_years:
                matched_requirements.append(
                    RequirementEvidence(
                        requirement=f"Experience ({min_experience_years}+ years required)",
                        evidence=f"Candidate possesses estimated {candidate_exp} years of relevant experience.",
                        confidence=0.9,
                        matched=True
                    )
                )
            else:
                missing_or_unclear.append(f"Experience: Has {candidate_exp} yrs, requires {min_experience_years} yrs")
                review_flags.append(f"Candidate experience ({candidate_exp} yrs) is below stated threshold ({min_experience_years} yrs)")

        return {
            "matched_requirements": matched_requirements,
            "missing_or_unclear_requirements": missing_or_unclear,
            "review_flags": review_flags
        }

job_matcher_agent = JobMatcherAgent()
