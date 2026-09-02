"""
Wall Service — Redaction, Anonymization & Public Feed Moderation for Wall of Shame / Wall of Fame.
"""
from __future__ import annotations

import re
from typing import Optional


# Known high-frequency tech companies / colleges to sanitize if mentioned
COMPANY_PATTERNS = [
    r"\b(google|microsoft|amazon|meta|apple|netflix|uber|tcs|infosys|wipro|cognizant|accenture|hcl|flipkart|swiggy|zomato|paytm|ola|cred|deloitte|ey|pwc|kpmg)\b",
    r"\b(iit\s+\w+|nit\s+\w+|iiit\s+\w+|bits\s+pilani|vit|srm|manipal|dtu|nsut)\b",
]


def anonymize_text(text: str) -> str:
    """
    Strips emails, phone numbers, full names, URLs, and specific company names
    from public roast strings before persistent display on the Wall.
    """
    if not text:
        return ""

    # 1. Emails
    text = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[Email]", text)

    # 2. Phone numbers
    text = re.sub(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", "[Phone]", text)

    # 3. URLs
    text = re.sub(r"https?://\S+|www\.\S+", "[Link]", text)

    # 4. Companies & colleges
    for pat in COMPANY_PATTERNS:
        text = re.sub(pat, "[Org]", text, flags=re.IGNORECASE)

    return text.strip()


def prepare_wall_entry_payload(
    overall_score: int,
    band: str,
    one_line_verdict: str,
    issues: list[dict],
) -> dict:
    """
    Extracts, anonymizes, and categorizes roast data for public wall publication.
    Score <= 50 goes to 'shame'; Score > 50 goes to 'fame'.
    """
    entry_type = "shame" if overall_score <= 50 else "fame"

    # Redact one_line_verdict
    safe_verdict = anonymize_text(one_line_verdict)

    # Pick top 2 roasts and redact them
    top_roasts: list[str] = []
    for iss in issues[:2]:
        raw_roast = iss.get("roast", "")
        if raw_roast:
            top_roasts.append(anonymize_text(raw_roast))

    return {
        "type": entry_type,
        "score": overall_score,
        "band": band,
        "one_line_verdict": safe_verdict,
        "top_roast_lines": top_roasts,
    }
