from typing import Dict, Any, List

class ScreeningAgent:
    """
    Applies the recruiter-defined evaluation rubric to produce an explainable screening report.
    Does NOT evaluate protected personal characteristics.
    """

    def evaluate(
        self,
        candidate_profile: Dict[str, Any],
        matching_result: Dict[str, Any],
        job_requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        required_skills: List[str] = job_requirements.get("required_skills", [])
        preferred_skills: List[str] = job_requirements.get("preferred_skills", [])
        min_exp = float(job_requirements.get("min_experience_years", 0))
        candidate_exp = float(candidate_profile.get("experience_years", 0.0))
        rubric: Dict[str, float] = job_requirements.get("rubric", {})

        skills_weight = rubric.get("skills_weight", 0.5)
        exp_weight = rubric.get("experience_weight", 0.3)
        proj_weight = rubric.get("projects_weight", 0.2)

        matched_reqs = matching_result.get("matched_requirements", [])
        missing_reqs = matching_result.get("missing_or_unclear_requirements", [])
        review_flags = list(matching_result.get("review_flags", []))

        # 1. Skills Score Calculation
        total_skills_count = len(required_skills) + (0.5 * len(preferred_skills))
        if total_skills_count > 0:
            matched_score_units = sum(
                1.0 if "(Required)" in r.requirement else 0.5
                for r in matched_reqs
                if "Experience" not in r.requirement
            )
            skills_pct = min(100.0, (matched_score_units / total_skills_count) * 100.0)
        else:
            skills_pct = 85.0

        # 2. Experience Score Calculation
        if min_exp > 0:
            exp_pct = min(100.0, (candidate_exp / min_exp) * 100.0)
        else:
            exp_pct = 90.0

        # 3. Projects Relevance Score
        projects = candidate_profile.get("projects", [])
        proj_pct = 75.0 if len(projects) >= 2 else (50.0 if len(projects) == 1 else 30.0)

        # Composite Match Score
        composite_score = round(
            (skills_pct * skills_weight) + (exp_pct * exp_weight) + (proj_pct * proj_weight),
            1
        )

        # Determine Recommendation Category
        has_critical_missing = any("required" in f.lower() for f in review_flags)
        
        if composite_score >= 80.0 and not has_critical_missing:
            recommendation = "Strong Match"
            rationale = (
                f"Candidate satisfies key technical requirements with an overall rubric score of {composite_score}%. "
                f"Identified strong alignment across skills ({skills_pct:.0f}%) and experience ({exp_pct:.0f}%)."
            )
        elif composite_score >= 60.0 or (composite_score >= 50.0 and not has_critical_missing):
            recommendation = "Potential Match"
            rationale = (
                f"Candidate meets core qualifications with a score of {composite_score}%. "
                f"Certain preferred skills or depth of experience may benefit from recruiter review."
            )
        elif has_critical_missing:
            recommendation = "Needs Clarification"
            rationale = (
                f"Candidate has promising background (Score: {composite_score}%), but one or more mandatory requirements "
                f"were not found in the resume. Manual clarification recommended."
            )
        else:
            recommendation = "Low Match"
            rationale = (
                f"Calculated match score of {composite_score}% indicates substantial variance from stated job criteria. "
                f"Recruiter review required before any adverse determination."
            )

        if candidate_profile.get("needs_manual_review"):
            review_flags.append("Resume parser flagged uncertainty in extracted fields.")

        return {
            "match_score": composite_score,
            "rubric_breakdown": {
                "skills_score": round(skills_pct, 1),
                "experience_score": round(exp_pct, 1),
                "projects_score": round(proj_pct, 1),
                "weights_used": {
                    "skills": skills_weight,
                    "experience": exp_weight,
                    "projects": proj_weight
                }
            },
            "recommendation": recommendation,
            "recommendation_rationale": rationale,
            "review_flags": review_flags
        }

screening_agent = ScreeningAgent()
