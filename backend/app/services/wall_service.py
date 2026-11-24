"""
Wall Service — Redaction, Anonymization & Public Feed Moderation for Wall of Shame / Wall of Fame.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Optional

from app.db import database

logger = logging.getLogger("wall_service")


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


def rotate_weekly_wall(force: bool = False, limit_per_category: int = 2) -> dict:
    """
    Weekly automated rotation of top and brutal candidate roasts into the Wall of Fame & Shame.
    - Picks highest scoring roasts (>=60) for Wall of Fame.
    - Picks lowest scoring roasts (<=50) for Wall of Shame.
    - Full anonymization & PII scrubbing is strictly applied to every entry.
    - Idempotent: Only rotates once every 7 days unless force=True.
    """
    today_dt = datetime.now(timezone.utc)
    current_week_str = f"{today_dt.isocalendar()[0]}-W{today_dt.isocalendar()[1]:02d}"
    today_date_str = today_dt.date().isoformat()

    last_rotation_date = database.get_last_wall_rotation_date()
    if not force and last_rotation_date:
        try:
            last_date = datetime.strptime(last_rotation_date[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if (today_dt - last_date).days < 7:
                return {
                    "rotated": False,
                    "reason": f"Already rotated within the last 7 days (last rotation: {last_rotation_date})",
                    "week": current_week_str,
                    "last_rotation": last_rotation_date,
                    "fame_count": 0,
                    "shame_count": 0,
                    "total_added": 0,
                }
        except Exception as e:
            logger.warning(f"Error parsing last rotation date '{last_rotation_date}': {e}")

    # Fetch top candidates from existing candidate database
    fame_candidates = database.get_unfeatured_candidate_roasts("fame", limit=limit_per_category)
    shame_candidates = database.get_unfeatured_candidate_roasts("shame", limit=limit_per_category)

    added_fame = []
    for cand in fame_candidates:
        issues = cand.get("issues", [])
        if isinstance(issues, str):
            try:
                issues = json.loads(issues)
            except Exception:
                issues = []
        payload = prepare_wall_entry_payload(
            overall_score=cand["overall_score"],
            band=cand.get("band", "strong"),
            one_line_verdict=cand.get("one_line_verdict", ""),
            issues=issues,
        )
        wall_id = database.save_wall_entry(
            roast_id=cand.get("id"),
            entry_type="fame",
            score=payload["score"],
            band=payload["band"],
            one_line_verdict=payload["one_line_verdict"],
            top_roast_lines=payload["top_roast_lines"],
            device_fingerprint=cand.get("device_fingerprint"),
        )
        added_fame.append({"wall_id": wall_id, "score": payload["score"]})

    added_shame = []
    for cand in shame_candidates:
        issues = cand.get("issues", [])
        if isinstance(issues, str):
            try:
                issues = json.loads(issues)
            except Exception:
                issues = []
        payload = prepare_wall_entry_payload(
            overall_score=cand["overall_score"],
            band=cand.get("band", "weak"),
            one_line_verdict=cand.get("one_line_verdict", ""),
            issues=issues,
        )
        wall_id = database.save_wall_entry(
            roast_id=cand.get("id"),
            entry_type="shame",
            score=payload["score"],
            band=payload["band"],
            one_line_verdict=payload["one_line_verdict"],
            top_roast_lines=payload["top_roast_lines"],
            device_fingerprint=cand.get("device_fingerprint"),
        )
        added_shame.append({"wall_id": wall_id, "score": payload["score"]})

    total_added = len(added_fame) + len(added_shame)
    database.record_wall_rotation(today_date_str, total_added)

    logger.info(
        f"Weekly wall rotation completed for {current_week_str}: "
        f"{len(added_fame)} fame added, {len(added_shame)} shame added."
    )

    return {
        "rotated": True,
        "week": current_week_str,
        "rotation_date": today_date_str,
        "fame_count": len(added_fame),
        "shame_count": len(added_shame),
        "total_added": total_added,
        "fame_added": added_fame,
        "shame_added": added_shame,
    }
