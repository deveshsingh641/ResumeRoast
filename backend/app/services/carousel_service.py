"""
LinkedIn Carousel PDF Generator Service
Generates an eye-catching, multi-page swipeable PDF carousel tailored
for LinkedIn document posts and social media sharing.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

logger = logging.getLogger(__name__)

CAROUSEL_DIR = Path(__file__).resolve().parent.parent.parent / "storage" / "carousels"
CAROUSEL_DIR.mkdir(parents=True, exist_ok=True)

# Color Palette (consistent with dark-terminal aesthetic)
BG_COLOR = HexColor("#0F0E0B")
CARD_BG = HexColor("#1A1814")
BORDER_COLOR = HexColor("#2D2922")
TEXT_PRIMARY = HexColor("#F5EFE0")
TEXT_SECONDARY = HexColor("#A69D89")
TEXT_MUTED = HexColor("#6B6455")
ACCENT_RED = HexColor("#E8422D")
ACCENT_AMBER = HexColor("#FFB93C")
ACCENT_GREEN = HexColor("#22C55E")


def _sanitize(text: str) -> str:
    """Filter out non-latin-1 characters and emojis for standard PDF fonts."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\x20-\x7E\xA0-\xFF]", "", text)
    return " ".join(cleaned.split())


def _wrap_text(text: str, max_chars: int = 55) -> List[str]:
    """Wrap text cleanly into lines respecting word boundaries."""
    words = text.split()
    lines: List[str] = []
    current: List[str] = []
    curr_len = 0

    for w in words:
        if curr_len + len(w) + 1 > max_chars and current:
            lines.append(" ".join(current))
            current = [w]
            curr_len = len(w)
        else:
            current.append(w)
            curr_len += len(w) + 1

    if current:
        lines.append(" ".join(current))
    return lines


def generate_linkedin_carousel_pdf(
    roast_id: str,
    roast_data: Dict[str, Any],
    app_url: str = "https://resume-roast-lemon.vercel.app",
) -> Path:
    """
    Renders a 3-slide, square (600x600 pt) high-resolution PDF document
    optimized for LinkedIn Carousel upload.
    """
    pdf_filename = f"carousel-{roast_id[:12]}.pdf"
    pdf_path = CAROUSEL_DIR / pdf_filename

    # If already cached, return immediately
    if pdf_path.exists() and pdf_path.stat().st_size > 1000:
        return pdf_path

    size = 600.0  # 600x600 square slide
    c = canvas.Canvas(str(pdf_path), pagesize=(size, size))

    score = int(roast_data.get("score") or 45)
    band = str(roast_data.get("band") or "MID").upper()
    verdict = _sanitize(str(roast_data.get("one_line_verdict") or "Your resume needs urgent CPR."))
    issues: List[Dict[str, Any]] = roast_data.get("issues") or []
    strengths: List[str] = roast_data.get("strengths") or []

    badge_color = ACCENT_RED if score < 45 else ACCENT_AMBER if score < 75 else ACCENT_GREEN

    # -------------------------------------------------------------
    # SLIDE 1: Cover Slide (The Hook & Overall Score)
    # -------------------------------------------------------------
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, size, size, fill=1, stroke=0)

    # Decorative Border
    c.setStrokeColor(BORDER_COLOR)
    c.setLineWidth(2)
    c.roundRect(24, 24, size - 48, size - 48, 12, fill=0, stroke=1)

    # Top Brand Header
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(ACCENT_AMBER)
    c.drawString(48, size - 64, "RESUMEROAST.AI")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(48, size - 80, "AI AUDIT & RECRUITER REALITY CHECK")

    c.drawRightString(size - 48, size - 64, "SLIDE 01 / 03")
    c.drawRightString(size - 48, size - 80, "SWIPE ->")

    # Big Hook Headline
    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(48, size - 140, "I Let AI Brutally Roast")
    c.drawString(48, size - 172, "My Tech Resume.")

    # Score Card Container
    c.setFillColor(CARD_BG)
    c.setStrokeColor(BORDER_COLOR)
    c.roundRect(48, size - 360, size - 96, 160, 10, fill=1, stroke=1)

    c.setFont("Helvetica", 12)
    c.setFillColor(TEXT_SECONDARY)
    c.drawString(72, size - 232, "OVERALL RESUME SCORE")

    # Large Score Display
    c.setFont("Helvetica-Bold", 64)
    c.setFillColor(badge_color)
    c.drawString(72, size - 304, f"{score}")
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(TEXT_MUTED)
    c.drawString(160, size - 280, "/ 100")

    # Tier Badge
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(badge_color)
    c.drawString(72, size - 336, f"[ TIER: {band} ]")

    # Savage One-Line Verdict
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(TEXT_MUTED)
    c.drawString(48, size - 395, "EXECUTIVE VERDICT:")

    c.setFont("Helvetica-Oblique", 13)
    c.setFillColor(TEXT_PRIMARY)
    verdict_lines = _wrap_text(f'"{verdict}"', max_chars=48)
    y_text = size - 420
    for line in verdict_lines[:3]:
        c.drawString(48, y_text, line)
        y_text -= 18

    # Bottom Swipe CTA
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ACCENT_AMBER)
    c.drawCentredString(size / 2, 46, "SWIPE TO SEE THE HARSH TRUTHS  ->")
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 2: The Red Flags (Top 3 Weakest Points)
    # -------------------------------------------------------------
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, size, size, fill=1, stroke=0)
    c.setStrokeColor(BORDER_COLOR)
    c.setLineWidth(2)
    c.roundRect(24, 24, size - 48, size - 48, 12, fill=0, stroke=1)

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(ACCENT_RED)
    c.drawString(48, size - 64, "THE RED FLAGS")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(48, size - 80, "WHAT ALMOST GOT THIS RESUME DISCARDED")
    c.drawRightString(size - 48, size - 64, "SLIDE 02 / 03")

    y_pos = size - 120
    flagged = issues[:3] if issues else [
        {"quoted_text": "Responsible for managing day to day tasks", "roast": "Generic filler phrase that states duty instead of impact."},
        {"quoted_text": "Passionate team player and self-starter", "roast": "High-density buzzwords with zero verifiable evidence."},
        {"quoted_text": "Worked on backend microservices", "roast": "Missing scale, latency metrics, and tech stack details."}
    ]

    for idx, item in enumerate(flagged, 1):
        q = _sanitize(item.get("quoted_text") or "Generic statement")
        r = _sanitize(item.get("roast") or "Lacks concrete quantifiable achievements.")

        # Card Box
        c.setFillColor(CARD_BG)
        c.setStrokeColor(BORDER_COLOR)
        c.roundRect(48, y_pos - 100, size - 96, 105, 8, fill=1, stroke=1)

        # Flag Badge
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(ACCENT_RED)
        c.drawString(64, y_pos - 20, f"FLAG #{idx} : WEAK CLAIM")

        # Quoted text
        c.setFont("Helvetica-Oblique", 11)
        c.setFillColor(TEXT_PRIMARY)
        q_lines = _wrap_text(f'"{q}"', max_chars=48)
        c.drawString(64, y_pos - 40, q_lines[0] if q_lines else '""')

        # Critique
        c.setFont("Helvetica", 10)
        c.setFillColor(TEXT_SECONDARY)
        r_lines = _wrap_text(f"Critique: {r}", max_chars=52)
        r_y = y_pos - 62
        for r_line in r_lines[:2]:
            c.drawString(64, r_y, r_line)
            r_y -= 14

        y_pos -= 125

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ACCENT_AMBER)
    c.drawCentredString(size / 2, 46, "SWIPE FOR THE FINAL VERDICT & FIXES  ->")
    c.showPage()

    # -------------------------------------------------------------
    # SLIDE 3: The Verdict & Action Checklist
    # -------------------------------------------------------------
    c.setFillColor(BG_COLOR)
    c.rect(0, 0, size, size, fill=1, stroke=0)
    c.setStrokeColor(BORDER_COLOR)
    c.setLineWidth(2)
    c.roundRect(24, 24, size - 48, size - 48, 12, fill=0, stroke=1)

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(ACCENT_GREEN)
    c.drawString(48, size - 64, "THE TURNAROUND")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(48, size - 80, "HOW TO FIX IT BEFORE APPLYING")
    c.drawRightString(size - 48, size - 64, "SLIDE 03 / 03")

    # Recommendations Container
    c.setFillColor(CARD_BG)
    c.setStrokeColor(BORDER_COLOR)
    c.roundRect(48, size - 380, size - 96, 280, 10, fill=1, stroke=1)

    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(TEXT_PRIMARY)
    c.drawString(72, size - 130, "Immediate Action Checklist:")

    checklist = [
        "1. Quantify Impact: Replace vague claims with numbers (%, $, latency, scale).",
        "2. Kill Fluff: Purge buzzwords ('self-starter', 'passionate', 'hardworking').",
        "3. Lead with Action: Begin every bullet with decisive power verbs.",
        "4. Align with ATS: Mirror target job description skills in active context.",
    ]

    check_y = size - 170
    for item in checklist:
        c.setFont("Helvetica", 11)
        c.setFillColor(TEXT_SECONDARY)
        c.drawString(72, check_y, item[:58])
        check_y -= 36

    # Strengths if present
    if strengths:
        clean_s = _sanitize(strengths[0])
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(ACCENT_GREEN)
        c.drawString(72, size - 340, f"[+] Strong Point: {clean_s[:48]}")

    # Bottom Branding & Link
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawCentredString(size / 2, 70, "Want your resume roasted by AI?")
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(ACCENT_AMBER)
    c.drawCentredString(size / 2, 48, app_url.replace("https://", ""))

    c.showPage()
    c.save()

    return pdf_path
