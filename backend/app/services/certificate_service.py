"""
Certificate Generation Service
Generates parody 'Official Certificate of Evaluation' as a high-resolution PDF.
"""
from __future__ import annotations

import os
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

# Storage path for generated certificates
CERTIFICATE_DIR = Path(__file__).resolve().parent.parent.parent / "storage" / "certificates"
CERTIFICATE_DIR.mkdir(parents=True, exist_ok=True)

# Credential titles mapped to score bands (Section 1.2)
CREDENTIAL_TITLES = {
    "weak": [  # 0 - 40
        "Bachelor of Buzzwords",
        "Diploma in Vague Achievements",
        "Fellow in Corporate Fluff",
        "Associate of Unquantified Claims",
    ],
    "mid": [   # 41 - 70
        "Associate Degree in Almost There",
        "Higher Diploma in Galti Se Mistake",
        "Certificate of Half-Baked Bullet Points",
        "Practitioner of Passive Voice",
    ],
    "strong": [ # 71 - 100
        "Bachelor of Actually Decent Bullet Points",
        "Honorary Degree in Quantifiable Impact",
        "Certified Not-Completely-Useless Resume",
        "PhD in Not Wasting a Recruiter's Time",
    ],
}


def get_credential_title(score: int, band: str, seed: Optional[str] = None) -> str:
    """Select a deterministic yet varied credential title based on score and seed."""
    normalized_band = band.lower()
    if normalized_band not in CREDENTIAL_TITLES:
        normalized_band = "weak" if score <= 40 else "mid" if score <= 70 else "strong"
    
    titles = CREDENTIAL_TITLES[normalized_band]
    if seed:
        idx = sum(ord(c) for c in seed) % len(titles)
        return titles[idx]
    return random.choice(titles)


def generate_certificate_pdf(
    *,
    roast_id: str,
    candidate_name: str = "Anonymous Candidate",
    score: int = 22,
    band: str = "weak",
    one_line_verdict: str = "Bhai ye resume hai ya birthday card ka message? 🎂",
    created_at: Optional[str] = None,
    is_pro: bool = False,
    language: str = "en",
) -> str:
    """
    Renders an ornate parody certificate and saves it to storage.
    Returns the absolute path to the generated PDF file.
    """
    from app.i18n.mapping import normalize_language
    lang = normalize_language(language)
    pdf_filename = f"certificate-{roast_id}-{lang}{'-pro' if is_pro else ''}.pdf"
    pdf_path = CERTIFICATE_DIR / pdf_filename

    # If cached version exists, return it
    if pdf_path.exists() and pdf_path.stat().st_size > 500:
        return str(pdf_path)

    # Date formatting
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.now(timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    date_str = dt.strftime("%B %d, %Y")

    # Dimensions: A4 Landscape (841.89 x 595.28 pt)
    width, height = landscape(A4)
    c = canvas.Canvas(str(pdf_path), pagesize=(width, height))

    # Palette
    c_parchment = HexColor("#FAF6EC")
    c_dark_ink   = HexColor("#1E1A16")
    c_burgundy   = HexColor("#5E1914")
    c_gold       = HexColor("#B8860B")
    c_gold_light = HexColor("#D4AF37")
    c_stamp_red  = HexColor("#D32F2F")
    c_tan_muted  = HexColor("#736B5E")

    # 1. Background Fill
    c.setFillColor(c_parchment)
    c.rect(0, 0, width, height, stroke=0, fill=1)

    # 2. Outer Ornate Border
    margin = 28
    c.setStrokeColor(c_burgundy)
    c.setLineWidth(4)
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    # Inner Gold Border
    c.setStrokeColor(c_gold)
    c.setLineWidth(1.5)
    c.rect(margin + 6, margin + 6, width - 2 * (margin + 6), height - 2 * (margin + 6))

    # Fine Double Inset
    c.setStrokeColor(c_burgundy)
    c.setLineWidth(0.75)
    c.rect(margin + 10, margin + 10, width - 2 * (margin + 10), height - 2 * (margin + 10))

    # Corner Rosettes / Flourishes
    corner_inset = margin + 18
    for cx, cy in [
        (corner_inset, corner_inset),
        (width - corner_inset, corner_inset),
        (corner_inset, height - corner_inset),
        (width - corner_inset, height - corner_inset),
    ]:
        c.setFillColor(c_gold)
        c.circle(cx, cy, 4, stroke=0, fill=1)
        c.setStrokeColor(c_burgundy)
        c.circle(cx, cy, 7, stroke=1, fill=0)

    # 3. Header Typography
    center_x = width / 2.0
    c.setFillColor(c_burgundy)
    c.setFont("Times-Bold", 14)
    c.drawCentredString(center_x, height - 68, "RESUME ROAST // BOARD OF RED PEN")

    c.setFillColor(c_gold)
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(center_x, height - 84, "— OFFICIAL CERTIFICATE OF EVALUATION —")

    # Decorative Rule Under Header
    c.setStrokeColor(c_gold_light)
    c.setLineWidth(1)
    c.line(center_x - 140, height - 92, center_x + 140, height - 92)

    # 4. Certification Text
    c.setFillColor(c_tan_muted)
    c.setFont("Times-Italic", 12)
    c.drawCentredString(center_x, height - 124, "This is to certify that")

    # Candidate Name
    c.setFillColor(c_dark_ink)
    c.setFont("Times-Bold", 26)
    name_display = candidate_name.upper().strip() or "ANONYMOUS CANDIDATE"
    c.drawCentredString(center_x, height - 156, name_display)

    # Subtle line under name
    c.setStrokeColor(c_burgundy)
    c.setLineWidth(1)
    c.line(center_x - 180, height - 164, center_x + 180, height - 164)

    # Body
    c.setFillColor(c_dark_ink)
    c.setFont("Times-Roman", 12)
    c.drawCentredString(center_x, height - 192, "has been rigorously examined by the Board of Red Pen and awarded an overall score of")

    # Score Box / Badge in Center
    c.setFillColor(c_stamp_red)
    c.setFont("Helvetica-Bold", 34)
    c.drawCentredString(center_x, height - 238, f"{score} / 100")

    # Discipline / Credential Title
    credential_title = get_credential_title(score, band, roast_id)
    c.setFillColor(c_tan_muted)
    c.setFont("Times-Italic", 12)
    c.drawCentredString(center_x, height - 268, "in the discipline of")

    c.setFillColor(c_burgundy)
    c.setFont("Times-BoldItalic", 20)
    c.drawCentredString(center_x, height - 296, credential_title)

    # Official Verdict Quote
    c.setFillColor(c_dark_ink)
    c.setFont("Helvetica-Oblique", 11)
    # Truncate verdict if excessively long to prevent layout overflow
    clean_verdict = one_line_verdict.strip().replace('"', '')
    if len(clean_verdict) > 85:
        clean_verdict = clean_verdict[:82] + "..."
    c.drawCentredString(center_x, height - 334, f'Official Verdict: "{clean_verdict}"')

    # 5. Stamp / Wax Seal Representation (Right Side)
    seal_x = width - 150
    seal_y = 125
    c.setFillColor(c_stamp_red)
    c.setStrokeColor(c_stamp_red)
    c.setLineWidth(3)
    c.circle(seal_x, seal_y, 44, stroke=1, fill=0)
    c.setLineWidth(1)
    c.circle(seal_x, seal_y, 40, stroke=1, fill=0)

    # Inside Stamp Text
    if lang == "hi-IN":
        band_label = "KAMZOR" if band == "weak" else "THIK-THAK" if band == "mid" else "DAMDAAR"
    else:
        band_label = "CRITICAL" if band == "weak" else "NEEDS WORK" if band == "mid" else "STRONG"
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(seal_x, seal_y + 8, str(score))
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(seal_x, seal_y - 8, band_label)
    c.setFont("Helvetica-Bold", 6)
    c.drawCentredString(seal_x, seal_y - 20, "★ RED PEN ★")

    # 6. Bottom Signatures & Dates
    sig_y = 110

    # Left: Date
    c.setStrokeColor(c_dark_ink)
    c.setLineWidth(1)
    c.line(100, sig_y + 15, 260, sig_y + 15)
    c.setFillColor(c_dark_ink)
    c.setFont("Times-Roman", 11)
    c.drawCentredString(180, sig_y + 22, date_str)
    c.setFont("Times-Italic", 9)
    c.drawCentredString(180, sig_y + 2, "Date of Evaluation")

    # Center: Chief Roasting Officer Signature
    c.line(center_x - 90, sig_y + 15, center_x + 90, sig_y + 15)
    c.setFont("Times-BoldItalic", 14)
    c.setFillColor(c_burgundy)
    c.drawCentredString(center_x, sig_y + 24, "Chief Roasting Officer")
    c.setFont("Times-Italic", 9)
    c.setFillColor(c_dark_ink)
    c.drawCentredString(center_x, sig_y + 2, "Board of Red Pen, Resume Roast")

    # 7. Watermark / Footer
    if not is_pro:
        c.setFillColor(c_tan_muted)
        c.setFont("Helvetica", 8)
        c.drawCentredString(center_x, margin + 12, "Official Parody Document · Verify & Roast your own resume at resumeroast.app")

    c.showPage()
    c.save()
    return str(pdf_path)
