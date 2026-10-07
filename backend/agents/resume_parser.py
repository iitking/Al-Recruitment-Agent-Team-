import re
from typing import Dict, Any, List
from backend.services.llm_service import llm_service
from backend.schemas.candidate import ParsedProfile

from backend.prompts import PARSE_RESUME_SYSTEM_PROMPT, PARSE_RESUME_USER_PROMPT

COMMON_TECH_SKILLS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI", "Django",
    "Flask", "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker", "Kubernetes",
    "AWS", "GCP", "Azure", "Git", "Machine Learning", "Deep Learning", "TensorFlow",
    "PyTorch", "NLP", "Pandas", "NumPy", "Scikit-Learn", "C++", "Java", "Go",
    "Rust", "HTML", "CSS", "TailwindCSS", "Next.js", "GraphQL", "REST API", "Linux",
    "CI/CD", "DevOps", "Microservices", "Data Science", "Computer Vision"
]

class ResumeParserAgent:
    """
    Parses unstructured resume text into a validated candidate profile.
    Uses LLM when configured, with high-accuracy heuristic extraction as fallback.
    """

    async def parse(self, raw_text: str) -> Dict[str, Any]:
        warnings: List[str] = []
        needs_review = False

        if not raw_text or len(raw_text.strip()) < 30:
            return {
                "name": "Unknown Candidate",
                "email": None,
                "phone": None,
                "profile": ParsedProfile(
                    skills=[],
                    experience_years=0.0,
                    education=[],
                    certifications=[],
                    employment_history=[],
                    projects=[],
                    extraction_warnings=["Resume text was empty or too short to parse reliably."],
                    needs_manual_review=True
                )
            }

        # Try LLM first if available
        llm_prompt = PARSE_RESUME_USER_PROMPT.format(raw_text=raw_text[:4000])
        llm_result = await llm_service.generate_json(
            system_prompt=PARSE_RESUME_SYSTEM_PROMPT,
            user_prompt=llm_prompt
        )

        if llm_result and "skills" in llm_result:
            name = llm_result.get("name")
            email = llm_result.get("email")
            phone = llm_result.get("phone")
            skills = llm_result.get("skills", [])
            exp_years = float(llm_result.get("experience_years", 0.0) or 0.0)
            edu = llm_result.get("education", [])
            certs = llm_result.get("certifications", [])
            history = llm_result.get("employment_history", [])
            projects = llm_result.get("projects", [])
            llm_warnings = llm_result.get("extraction_warnings", [])

            if not email:
                warnings.append("No email address could be extracted from resume.")
                needs_review = True
            if not skills:
                warnings.append("No skills identified in resume.")
                needs_review = True

            warnings.extend(llm_warnings)

            return {
                "name": name,
                "email": email,
                "phone": phone,
                "profile": ParsedProfile(
                    skills=skills,
                    experience_years=exp_years,
                    education=edu,
                    certifications=certs,
                    employment_history=history,
                    projects=projects,
                    extraction_warnings=warnings,
                    needs_manual_review=needs_review
                )
            }

        # Fallback Heuristic Extractor
        return self._heuristic_parse(raw_text)

    def _heuristic_parse(self, text: str) -> Dict[str, Any]:
        warnings: List[str] = []
        needs_review = False

        # Extract Email
        email_match = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
        email = email_match.group(0) if email_match else None
        if not email:
            warnings.append("Email address not found in resume.")
            needs_review = True

        # Extract Phone
        phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}', text)
        phone = phone_match.group(0) if phone_match else None

        # Extract Candidate Name (First non-empty line or header)
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        candidate_name = "Candidate"
        if lines:
            first_line = lines[0]
            if len(first_line.split()) <= 4 and not any(k in first_line.lower() for k in ["resume", "curriculum", "cv", "page"]):
                candidate_name = first_line
            elif len(lines) > 1 and len(lines[1].split()) <= 4:
                candidate_name = lines[1]

        # Extract Skills
        found_skills = set()
        text_lower = text.lower()
        for skill in COMMON_TECH_SKILLS:
            # Match word boundary
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)

        # Check Skills section
        skills_section = re.search(r'(?:skills|technical skills|technologies)[\s:]+([^\n]+(?:\n[^\n]+){1,3})', text, re.IGNORECASE)
        if skills_section:
            extracted_items = re.split(r'[,|•\*\n]+', skills_section.group(1))
            for item in extracted_items:
                clean_item = item.strip()
                if 2 <= len(clean_item) <= 25 and not clean_item.lower().startswith("http"):
                    found_skills.add(clean_item)

        skills_list = sorted(list(found_skills))
        if not skills_list:
            warnings.append("No technical skills detected in resume.")
            needs_review = True

        # Estimate Experience Years
        exp_matches = re.findall(r'(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+experience', text, re.IGNORECASE)
        exp_years = 0.0
        if exp_matches:
            try:
                exp_years = max(float(x) for x in exp_matches)
            except ValueError:
                exp_years = 2.0
        else:
            # Check year ranges like 2018 - 2022
            year_pairs = re.findall(r'(20\d\d)\s*[-–to]+\s*(20\d\d|present|current)', text, re.IGNORECASE)
            if year_pairs:
                total_span = 0
                current_year = 2026
                for y1, y2 in year_pairs:
                    start_yr = int(y1)
                    end_yr = current_year if y2.lower() in ["present", "current"] else int(y2)
                    if end_yr >= start_yr:
                        total_span += (end_yr - start_yr)
                exp_years = float(min(total_span, 30))

        # Extract Education
        education = []
        edu_patterns = [r'b\.?tech\w*', r'bachelor\w*', r'master\w*', r'm\.?tech\w*', r'b\.?s\w*', r'm\.?s\w*', r'ph\.?d\w*', r'degree']
        for line in lines:
            if any(re.search(p, line, re.IGNORECASE) for p in edu_patterns):
                if len(line) < 120 and line not in education:
                    education.append(line)

        # Extract Projects
        projects = []
        in_project_section = False
        for line in lines:
            if re.search(r'^(?:projects|key projects|academic projects)', line, re.IGNORECASE):
                in_project_section = True
                continue
            if in_project_section:
                if re.search(r'^(?:education|experience|skills|certifications|awards)', line, re.IGNORECASE):
                    break
                if len(line) > 15 and len(line) < 150:
                    projects.append(line)
                if len(projects) >= 4:
                    break

        return {
            "name": candidate_name,
            "email": email or f"candidate_{len(candidate_name)}@example.com",
            "phone": phone,
            "profile": ParsedProfile(
                skills=skills_list,
                experience_years=exp_years,
                education=education[:3],
                certifications=[],
                employment_history=[{"summary": f"Detected experience across {exp_years} years"}],
                projects=projects[:3],
                extraction_warnings=warnings,
                needs_manual_review=needs_review
            )
        }

resume_parser_agent = ResumeParserAgent()
