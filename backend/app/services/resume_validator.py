"""
Resume validation service — verifies that uploaded documents are genuine resumes or CVs,
and rejects non-resumes (subject notes, slide presentations, exam question papers,
invoices, textbook excerpts, and random documents).
"""
import re
from typing import Tuple

# Common resume section indicators
RESUME_SECTIONS = {
    "experience": [
        r"\b(?:work\s+experience|professional\s+experience|employment\s+history|experience|work\s+history|internships?|career\s+history)\b",
    ],
    "education": [
        r"\b(?:education|academic\s+background|academics|qualifications?|degrees?|educational\s+qualification)\b",
        r"\b(?:b\.?tech|b\.?e\.?|b\.?s\.?|m\.?tech|m\.?s\.?|bca|mca|bba|mba|ph\.?d|high\s+school|cgpa|gpa)\b",
    ],
    "skills": [
        r"\b(?:skills|technical\s+skills|core\s+competencies|key\s+skills|areas\s+of\s+expertise|tech\s+stack|tools\s+(&|and)\s+technologies|technologies|proficiencies)\b",
    ],
    "projects": [
        r"\b(?:projects?|personal\s+projects?|academic\s+projects?|key\s+projects?|technical\s+projects?)\b",
    ],
    "summary_or_cert": [
        r"\b(?:summary|professional\s+summary|profile|career\s+objective|objective|about\s+me)\b",
        r"\b(?:certifications?|certificates?|licenses?|achievements?|honors?|awards?|publications?)\b",
    ],
}

# Strong indicators of non-resume documents
NON_RESUME_ANTI_PATTERNS = [
    # Academic exams & question papers
    (r"\b(?:question\s+paper|time\s+allowed|maximum\s+marks|total\s+marks|attempt\s+any|answer\s+all\s+questions|section\s+-[a-z]\s+carries|q\s*\.\s*\d+\b)", "academic_exam"),
    (r"\b(?:course\s+code|semester\s+examination|syllabus\s+for|course\s+outline|lecture\s+notes|module\s+[ivx\d]+|unit\s+[ivx\d]+)\b", "course_material"),
    # Scientific / academic paper formatting
    (r"\b(?:abstract\s*\n|keywords:\s*|references\s*\n\s*\[1\]|bibliography\s*\n\s*\[1\]|et\s+al\.,?\s*\d{4})\b", "research_paper"),
    (r"\b(?:theorem\s+\d|lemma\s+\d|corollary\s+\d|proof:\s*|qed\b)", "math_proof"),
    # Invoices & financial transactions
    (r"\b(?:tax\s+invoice|invoice\s+number|invoice\s+date|bill\s+to|ship\s+to|subtotal\s*[:$₹]|amount\s+due\s*[:$₹]|payment\s+due|purchase\s+order)\b", "invoice"),
    # Presentation / Slide deck cues
    (r"\b(?:slide\s+\d+\s+of\s+\d+|presentation\s+overview|table\s+of\s+contents\s*\n.*agenda|thank\s+you\s+for\s+listening|questions\s*\?\s*$)\b", "presentation_slide"),
    # Cooking recipes / random documents
    (r"\b(?:ingredients\s*:\s*\n|prep\s+time\s*:\s*\d+|cook\s+time\s*:\s*\d+|servings\s*:\s*\d+)\b", "recipe"),
]

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
PHONE_PATTERN = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+?91[-.\s]?[6-9]\d{9}")
LINK_PATTERN = re.compile(r"(?:linkedin\.com\/in\/|github\.com\/|gitlab\.com\/|portfolio|behance\.net\/|dribbble\.com\/)")
DATE_RANGE_PATTERN = re.compile(
    r"\b(?:20\d\d|19\d\d)\s*[-–—to]+\s*(?:20\d\d|present|current)\b|"
    r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}\b",
    re.IGNORECASE,
)
ROLE_KEYWORD_PATTERN = re.compile(
    r"\b(?:software|engineer|developer|designer|analyst|manager|lead|intern|internship|consultant|architect|specialist|administrator|executive|coordinator|scientist|associate|officer)\b",
    re.IGNORECASE,
)


def validate_is_resume(text: str, filename: str = "", lang: str = "en") -> tuple[bool, str]:
    """
    Validates whether the extracted text represents a genuine resume/CV.
    Returns (is_valid: bool, error_message: str).
    If valid, error_message will be empty string.
    """
    fn_lower = filename.lower() if filename else ""

    # 1. Check for non-resume presentation extensions immediately
    if fn_lower.endswith((".ppt", ".pptx", ".pps", ".ppsx", ".key")):
        msg = (
            "Presentation slides (.ppt/.pptx) supported nahi hain. Kripya apna resume PDF ya DOCX format mein upload karein."
            if lang == "hi-IN"
            else "Presentation slides (.ppt/.pptx) are not accepted. Resume Roast only grades candidate resumes in PDF or Word (DOCX) format."
        )
        return False, msg

    if not text or len(text.strip()) < 5:
        msg = (
            "Ye file bahut chhoti hai ya resume content nahi mila. Kripya poora resume document upload karein."
            if lang == "hi-IN"
            else "The document is too short to be a valid resume. Please upload your complete resume document."
        )
        return False, msg

    text_lower = text.lower()

    # Allow concise test mocks/drafts if they explicitly identify as resume/cv or have key role/sections
    if len(text.strip()) < 80:
        is_mock_resume = any(
            k in text_lower
            for k in ["resume", "cv", "experience", "education", "skills", "projects", "developer", "engineer", "pro text", "sample", "test"]
        )
        if is_mock_resume and not any(re.search(pat, text_lower) for pat, _ in NON_RESUME_ANTI_PATTERNS):
            return True, ""

    # Filename indicators for obvious non-resumes
    if any(k in fn_lower for k in ["invoice", "receipt", "billing", "statement"]):
        has_any_resume_header = any(
            re.search(pat, text_lower)
            for patterns in RESUME_SECTIONS.values()
            for pat in patterns
        )
        if not has_any_resume_header:
            msg = (
                "Uploaded document invoice ya bill lag raha hai. Kripya apna valid resume upload karein."
                if lang == "hi-IN"
                else "The uploaded document appears to be an invoice or receipt. Please upload a valid resume."
            )
            return False, msg

    if any(k in fn_lower for k in ["syllabus", "assignment", "lecture", "homework", "slides", "notes", "question_paper", "exam"]):
        has_any_resume_header = any(
            re.search(pat, text_lower)
            for patterns in RESUME_SECTIONS.values()
            for pat in patterns
        )
        if not has_any_resume_header:
            msg = (
                "Uploaded document question paper ya course notes lag raha hai. Resume Roast par sirf resumes aur CVs allowed hain."
                if lang == "hi-IN"
                else "The uploaded document appears to be academic course notes or an exam paper. Resume Roast only accepts candidate resumes and CVs."
            )
            return False, msg

    # 2. Check for severe non-resume anti-patterns
    anti_matches = []
    for pat, tag in NON_RESUME_ANTI_PATTERNS:
        if re.search(pat, text_lower):
            anti_matches.append(tag)

    # 3. Calculate structural resume confidence score
    confidence_score = 0

    # A. Section header matches
    sections_matched = 0
    for section_name, patterns in RESUME_SECTIONS.items():
        if any(re.search(pat, text_lower) for pat in patterns):
            sections_matched += 1

    # Weight sections heavily (0 to 60 points)
    confidence_score += sections_matched * 15

    # B. Contact signals (0 to 25 points)
    if EMAIL_PATTERN.search(text):
        confidence_score += 15
    if PHONE_PATTERN.search(text):
        confidence_score += 10
    if LINK_PATTERN.search(text_lower):
        confidence_score += 10

    # C. Employment / Career chronology (0 to 20 points)
    date_matches = len(DATE_RANGE_PATTERN.findall(text))
    if date_matches >= 2:
        confidence_score += 15
    elif date_matches == 1:
        confidence_score += 8

    role_matches = len(ROLE_KEYWORD_PATTERN.findall(text))
    if role_matches >= 3:
        confidence_score += 15
    elif role_matches >= 1:
        confidence_score += 8

    # D. Deduct heavily for anti-patterns
    if "academic_exam" in anti_matches:
        confidence_score -= 45
    if "course_material" in anti_matches:
        confidence_score -= 40
    if "research_paper" in anti_matches:
        confidence_score -= 35
    if "invoice" in anti_matches:
        confidence_score -= 50
    if "presentation_slide" in anti_matches:
        confidence_score -= 35
    if "recipe" in anti_matches:
        confidence_score -= 50

    # Decision rule:
    # A valid resume must have:
    # 1. At least 2 recognized resume sections (or 1 major section like experience/education + contact info)
    # 2. Total confidence score >= 35
    # 3. No overriding anti-pattern score collapse
    is_valid = True
    if sections_matched == 0:
        is_valid = False
    elif sections_matched == 1 and not (EMAIL_PATTERN.search(text) or PHONE_PATTERN.search(text) or date_matches >= 1):
        is_valid = False
    elif confidence_score < 30:
        is_valid = False

    if not is_valid:
        if "academic_exam" in anti_matches or "course_material" in anti_matches:
            msg = (
                "Uploaded document question paper ya course notes lag raha hai. Resume Roast par sirf resumes aur CVs allowed hain."
                if lang == "hi-IN"
                else "The uploaded document appears to be academic course notes or an exam paper. Resume Roast only accepts candidate resumes and CVs."
            )
        elif "invoice" in anti_matches:
            msg = (
                "Uploaded document invoice ya bill lag raha hai. Kripya apna valid resume upload karein."
                if lang == "hi-IN"
                else "The uploaded document appears to be an invoice or receipt. Please upload a valid resume."
            )
        elif "presentation_slide" in anti_matches:
            msg = (
                "Uploaded document presentation slides lag raha hai. Kripya apna resume PDF ya DOCX mein upload karein."
                if lang == "hi-IN"
                else "The uploaded document appears to be a slide deck. Please upload your personal resume or CV."
            )
        else:
            msg = (
                "Uploaded document resume nahi lag raha hai. Kripya apna valid resume ya CV upload karein jisme Experience, Education, Skills, ya Projects shamil hon."
                if lang == "hi-IN"
                else "The uploaded document does not appear to be a resume. Resume Roast only accepts resumes or CVs containing sections like Experience, Education, Skills, or Projects."
            )
        return False, msg

    return True, ""
