"""
Test Fix Diversity & Anti-Repetition Engine
Ensures that multiple issues in a roast NEVER receive identical fix suggestions,
and that job titles / role headers are excluded from numberless bullet checks.
"""
import pytest
from app.services.ai_analyzer import _generate_fallback_roast, _generate_domain_fix, _is_role_or_header_line


def test_is_role_or_header_line():
    assert _is_role_or_header_line("Full-Stack Development Intern Remote") is True
    assert _is_role_or_header_line("Software Engineer | 2022 - Present") is True
    assert _is_role_or_header_line("Technical Skills:") is True
    assert _is_role_or_header_line("Education") is True
    assert _is_role_or_header_line("email: candidate@gmail.com") is True

    # Real accomplishment bullets should NOT be flagged as headers
    assert _is_role_or_header_line(
        "Designed JWT authentication and RBAC-driven CRUD workflows, hardened through peer review and iteration."
    ) is False
    assert _is_role_or_header_line(
        "Responsible for building responsive client interfaces using React and Tailwind CSS."
    ) is False


def test_fix_suggestions_never_repeat():
    used_fixes = set()
    line_auth = "Designed JWT authentication and RBAC-driven CRUD workflows"
    line_frontend = "Built user interface components with React and CSS"
    line_algo = "Implemented C++ data structures and search algorithms"
    line_backend = "Developed REST APIs and backend microservices"

    fix1 = _generate_domain_fix(line_auth, "engineering", "no-metrics", "en", used_fixes)
    fix2 = _generate_domain_fix(line_frontend, "engineering", "no-metrics", "en", used_fixes)
    fix3 = _generate_domain_fix(line_algo, "engineering", "no-metrics", "en", used_fixes)
    fix4 = _generate_domain_fix(line_backend, "engineering", "no-metrics", "en", used_fixes)

    fixes = [fix1, fix2, fix3, fix4]
    # All 4 fixes MUST be completely unique
    assert len(set(fixes)) == 4, f"Found duplicate fixes: {fixes}"

    # Verify context awareness
    assert "JWT" in fix1 or "security" in fix1.lower() or "auth" in fix1.lower()
    assert "React" in fix2 or "UI" in fix2 or "frontend" in fix2.lower()
    assert "C++" in fix3 or "algorithm" in fix3.lower() or "memory" in fix3.lower()


def test_candidate_resume_roast_has_distinct_fixes():
    candidate_resume = """
    Aakash Verma
    Email: aakash@example.com | Phone: +91 9876543210
    Full-Stack Development Intern Remote (2023 - Present)
    
    through internship and personal projects. Strong foundation in C++, Data Structures & Algorithms, React.js
    Designed JWT authentication and RBAC-driven CRUD workflows, hardened through peer review and iteration.
    Assisted team with writing documentation and managing client deliverables.
    Responsible for maintaining database queries and server endpoints.
    """

    res = _generate_fallback_roast(candidate_resume, language="hi-IN")
    issues = res.get("issues", [])
    assert len(issues) >= 2

    # Check that the job title was NOT picked as an issue
    quotes = [iss["quoted_text"] for iss in issues]
    assert not any("Full-Stack Development Intern Remote" in q for q in quotes), (
        "Job title should not be flagged as a flawed bullet point"
    )

    # Check that all fixes across all issues are 100% unique
    fixes = [iss["fix"] for iss in issues]
    assert len(fixes) == len(set(fixes)), f"Found duplicate fixes in roast: {fixes}"
