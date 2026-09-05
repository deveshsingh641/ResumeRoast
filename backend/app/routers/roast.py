"""
Roast router — handles resume upload, text extraction, deduplication, AI analysis, and retrieval.
"""
from __future__ import annotations

import hashlib
import os
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.db import database
from app.i18n.mapping import DEFAULT_LANGUAGE, language_from_request
from app.services import ai_analyzer, extractor
from app.services.certificate_service import generate_certificate_pdf, get_credential_title

SAMPLE_ROAST_RESPONSE = {
    "id": "demo",
    "overall_score": 28,
    "band": "weak",
    "one_line_verdict": "Bhai resume hai ya suspense novel? 🕵️",
    "issues": [
        {
            "quoted_text": "Responsible for building reusable UI components and collaborating across teams",
            "category": "no-metrics",
            "badge_label": "PROOF DE DO",
            "roast": "\"Responsible for\" likhna band karo yaar 😩 recruiter ko number chahiye, kahani nahi.",
            "fix": "Kuch is tarah likho: 'Built 12 reusable UI components, cutting page load time by 30%' — number daalo, impact dikhao.",
            "start_offset": 45,
            "end_offset": 125,
            "severity_rank": 1,
        },
        {
            "quoted_text": "Leveraged synergistic paradigms to accelerate core business outcomes",
            "category": "buzzword",
            "badge_label": "BUZZWORD OVERDOSE",
            "roast": "Ye word har second resume mein hai bhai, tu unique kaise banega isse?",
            "fix": "Corporate jargon cut karo aur seedha bolo: 'Led checkout redesign, reducing cart drop-off by 18%'.",
            "start_offset": 130,
            "end_offset": 200,
            "severity_rank": 2,
        },
        {
            "quoted_text": "DECLARATION: I hereby declare that all information is true to my knowledge",
            "category": "formatting",
            "badge_label": "FORMAT BIGDA HUA",
            "roast": "Bhai 2005 ka declaration kyu daal rakha hai? ✋ Modern tech resume mein iski zaroorat nahi hai.",
            "fix": "Declaration section poora delete kardo aur whitespace ko project links ke liye use karo.",
            "start_offset": 210,
            "end_offset": 285,
            "severity_rank": 3,
        },
        {
            "quoted_text": "Hobbies: Playing cricket, watching movies, listening to music",
            "category": "irrelevant",
            "badge_label": "YE KYUN LIKHA BHAI",
            "roast": "Ye yahan kyun hai bhai? Iska job se koi lena dena nahi 🤔",
            "fix": "Hobbies section hatao aur wahan hackathon rank ya open-source contributions mention karo.",
            "start_offset": 290,
            "end_offset": 350,
            "severity_rank": 4,
        },
        {
            "quoted_text": "Curriculum Vitae (Page 1 of 4) — Detailed Experience",
            "category": "length",
            "badge_label": "ITNA LAMBA KYUN",
            "roast": "Recruiter 6 second dekhta hai resume, tune usse 4 page bana diya.",
            "fix": "Isko 1 page mein fit karo. Purani schooling aur obvious baatein hatao.",
            "start_offset": 355,
            "end_offset": 405,
            "severity_rank": 5,
        },
        {
            "quoted_text": "SKILS: Pythno, Jacascript, C++",
            "category": "typo",
            "badge_label": "SPELLING MISS HAI",
            "roast": "Spelling mistake hai bhai, spellcheck bhi nahi chalaya kya? 😩",
            "fix": "Typo fix karo: 'Python, JavaScript, C++' — submission se pehle ek baar Grammarly zaroor run karo.",
            "start_offset": 410,
            "end_offset": 440,
            "severity_rank": 6,
        },
    ],
    "total_issues": 6,
    "strengths": [
        "Tech stack modern hai — FastAPI aur React achha combination hai 🚀",
        "Projects section mein GitHub links live hain 🔥",
    ],
    "is_truncated": False,
    "created_at": "2026-09-01T12:00:00Z",
}

ENGLISH_SAMPLE_ROAST_RESPONSE = {
    "id": "demo",
    "overall_score": 28,
    "band": "weak",
    "one_line_verdict": "Is this a resume or a mystery novel? Let's see some evidence 🕵️",
    "issues": [
        {
            "quoted_text": "Responsible for building reusable UI components and collaborating across teams",
            "category": "no-metrics",
            "badge_label": "WHERE IS PROOF",
            "roast": "This line has a verb and a shrug. Zero numbers and the recruiter keeps scrolling 📉",
            "fix": "Quantify this: 'Built 12 reusable UI components in React/TS, reducing average page load time by 30%'.",
            "start_offset": 45,
            "end_offset": 125,
            "severity_rank": 1,
        },
        {
            "quoted_text": "Leveraged synergistic paradigms to accelerate core business outcomes",
            "category": "buzzword",
            "badge_label": "BUZZWORD OVERLOAD",
            "roast": "Every resume on earth says this. Recruiters stopped reading it as information around 2015 🤖",
            "fix": "Cut the corporate jargon and write: 'Led checkout redesign, reducing cart abandonment rate by 18%'.",
            "start_offset": 130,
            "end_offset": 200,
            "severity_rank": 2,
        },
        {
            "quoted_text": "DECLARATION: I hereby declare that all information is true to my knowledge",
            "category": "formatting",
            "badge_label": "FORMATTING CHAOS",
            "roast": "Declarations and signatures retired in 2005. Don't spend premium whitespace on legal disclaimers ✋",
            "fix": "Delete the entire declaration section and use the space for live portfolio or GitHub project links.",
            "start_offset": 210,
            "end_offset": 285,
            "severity_rank": 3,
        },
        {
            "quoted_text": "Hobbies: Playing cricket, watching movies, listening to music",
            "category": "irrelevant",
            "badge_label": "OUT OF PLACE",
            "roast": "Was this detail required, or did it just wander in? A recruiter does not need to know this 🤔",
            "fix": "Remove hobbies and highlight hackathon achievements, certifications, or open-source PRs.",
            "start_offset": 290,
            "end_offset": 350,
            "severity_rank": 4,
        },
        {
            "quoted_text": "Curriculum Vitae (Page 1 of 4) — Detailed Experience",
            "category": "length",
            "badge_label": "TRIM THE FAT",
            "roast": "Recruiters give this six seconds. You gave them a four-page novella 📚",
            "fix": "Condense to a single sharp page. Remove outdated schooling and obvious generic job duties.",
            "start_offset": 355,
            "end_offset": 405,
            "severity_rank": 5,
        },
        {
            "quoted_text": "SKILS: Pythno, Jacascript, C++",
            "category": "typo",
            "badge_label": "SPELLCHECK FAILED",
            "roast": "One typo and 'detail-oriented' becomes a joke at your expense 😩",
            "fix": "Correct spelling: 'Python, JavaScript, C++' — run spellcheck before submitting any application.",
            "start_offset": 410,
            "end_offset": 440,
            "severity_rank": 6,
        },
    ],
    "total_issues": 6,
    "strengths": [
        "Modern tech stack highlighted — FastAPI and React are an attractive combination 🚀",
        "Direct GitHub links included under key project entries 🔥",
    ],
    "is_truncated": False,
    "created_at": "2026-09-01T12:00:00Z",
}

router = APIRouter(prefix="/api", tags=["roast"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
FREE_TIER_LIMIT = int(os.getenv("FREE_TIER_DAILY_LIMIT", "1"))


def _device_fingerprint(request: Request) -> str:
    """
    Generate a semi-stable anonymous fingerprint from IP + User-Agent.
    Gracefully falls back to client host if forwarded headers are absent.
    """
    custom_fp = request.headers.get("X-Device-Fingerprint")
    if custom_fp:
        return custom_fp
    forwarded = request.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
    ua = request.headers.get("User-Agent", "standard-browser")
    raw = f"{ip}:{ua}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@router.post("/roast")
async def create_roast(
    request: Request,
    file: UploadFile = File(...),
) -> JSONResponse:
    filename = file.filename or "resume.pdf"
    content_type = file.content_type or ""

    # 1. Read bytes & validate size
    try:
        file_bytes = await file.read()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="File upload was interrupted. Please check your connection and upload again.",
        )

    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=422,
            detail="That file is empty (0 bytes). Please upload a complete resume document.",
        )

    if len(file_bytes) > MAX_FILE_SIZE:
        size_mb = f"{len(file_bytes) / 1024 / 1024:.1f}"
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb}MB). Maximum supported size is 5MB.",
        )

    # 2. Rate-limit & Pro subscription check (server-enforced)
    user_email = request.headers.get("X-User-Email") or request.query_params.get("email")
    is_pro = False
    if user_email:
        clean_email = user_email.strip().lower()
        is_pro = (database.get_user_subscription(clean_email) == "pro")

    is_free_tier = not is_pro
    fingerprint = _device_fingerprint(request)
    usage_count = database.get_usage_count(fingerprint)

    if is_free_tier and usage_count >= FREE_TIER_LIMIT:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "daily_limit_reached",
                "message": (
                    f"You have used your {FREE_TIER_LIMIT} free roast for today. "
                    "Upgrade to Pro for unlimited daily roasts."
                ),
                "upgrade_url": "/pricing",
            },
        )

    # 3. Deduplication check (avoid double processing on rapid double-clicks from the same user/device)
    lang = language_from_request(request)
    content_hash = hashlib.sha256(file_bytes + b":" + fingerprint.encode() + b":" + lang.encode()).hexdigest()
    existing_roast_id = database.check_dedup(content_hash)
    if existing_roast_id:
        existing_roast = database.get_roast(existing_roast_id)
        if existing_roast and "overall_score" in existing_roast:
            import json as _json
            issues = existing_roast.get("issues") or []
            if isinstance(issues, str):
                try:
                    issues = _json.loads(issues)
                except Exception:
                    issues = []
            strengths = existing_roast.get("strengths") or []
            if isinstance(strengths, str):
                try:
                    strengths = _json.loads(strengths)
                except Exception:
                    strengths = []

            issues = issues or []
            strengths = strengths or []

            return JSONResponse(
                content={
                    "id": existing_roast_id,
                    "overall_score": existing_roast["overall_score"],
                    "band": existing_roast.get("band", "mid"),
                    "one_line_verdict": existing_roast.get("one_line_verdict", ""),
                    "issues": issues[:3] if is_free_tier else issues,
                    "total_issues": len(issues),
                    "strengths": strengths,
                    "is_truncated": is_free_tier and len(issues) > 3,
                }
            )

    # 4. Extract text & validate magic bytes
    try:
        resume_text, was_truncated = extractor.extract_text(filename, content_type, file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Failed to read your document. Try exporting it fresh as a PDF or standard DOCX.",
        )

    # 5. AI analysis
    try:
        analysis = ai_analyzer.analyze_resume(resume_text, language=lang)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Our AI grader encountered an unexpected error. Please try again in a few moments.",
        )

    # 6. Increment usage counter
    database.increment_usage(fingerprint)

    # 7. Store result
    roast_id = database.save_roast(
        overall_score=analysis["overall_score"],
        band=analysis["band"],
        one_line_verdict=analysis["one_line_verdict"],
        issues=analysis["issues"],
        strengths=analysis["strengths"],
        device_fingerprint=fingerprint,
        resume_text=resume_text,
    )

    # Register in dedup cache
    database.register_dedup(content_hash, roast_id)

    # 8. Build response
    all_issues = analysis["issues"]
    is_truncated = is_free_tier and len(all_issues) > 3
    visible_issues = all_issues[:3] if is_free_tier else all_issues

    return JSONResponse(
        content={
            "id": roast_id,
            "overall_score": analysis["overall_score"],
            "band": analysis["band"],
            "one_line_verdict": analysis["one_line_verdict"],
            "issues": visible_issues,
            "total_issues": len(all_issues),
            "strengths": analysis["strengths"],
            "is_truncated": is_truncated,
            "was_document_truncated": was_truncated,
        }
    )


@router.get("/roast/demo")
async def get_demo_roast(request: Request) -> JSONResponse:
    lang = language_from_request(request)
    demo_data = SAMPLE_ROAST_RESPONSE if lang == "hi-IN" else ENGLISH_SAMPLE_ROAST_RESPONSE
    return JSONResponse(content=demo_data)


@router.get("/roast/{roast_id}")
async def get_roast(roast_id: str, request: Request, email: Optional[str] = None) -> JSONResponse:
    # Check if request comes with Pro user identification
    user_email = email or request.headers.get("X-User-Email")
    is_pro = False
    if user_email:
        is_pro = (database.get_user_subscription(user_email.strip().lower()) == "pro")

    if roast_id in ("demo", "demo-roast", "sample-roast-1"):
        lang = language_from_request(request)
        demo_source = SAMPLE_ROAST_RESPONSE if lang == "hi-IN" else ENGLISH_SAMPLE_ROAST_RESPONSE
        demo_resp = dict(demo_source)
        if is_pro:
            demo_resp["is_truncated"] = False
        return JSONResponse(content=demo_resp)

    row = database.get_roast(roast_id)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail="This roast is not found or has expired (anonymous roasts are purged after 7 days).",
        )

    import json as _json
    issues = row.get("issues", [])
    if isinstance(issues, str):
        try:
            issues = _json.loads(issues)
        except Exception:
            issues = []

    strengths = row.get("strengths", [])
    if isinstance(strengths, str):
        try:
            strengths = _json.loads(strengths)
        except Exception:
            strengths = []

    issues = issues or []
    strengths = strengths or []

    is_truncated = (len(issues) > 3) and (not is_pro)
    visible_issues = issues if is_pro else issues[:3]

    return JSONResponse(
        content={
            "id": str(row["id"]),
            "overall_score": row["overall_score"],
            "band": row["band"],
            "one_line_verdict": row["one_line_verdict"],
            "issues": visible_issues,
            "total_issues": len(issues),
            "strengths": strengths,
            "is_truncated": is_truncated,
            "created_at": str(row.get("created_at", "")),
        }
    )


@router.get("/roast/{roast_id}/certificate")
async def get_certificate_info(roast_id: str) -> JSONResponse:
    if roast_id in ("demo", "demo-roast", "sample-roast-1"):
        row = SAMPLE_ROAST_RESPONSE
    else:
        row = database.get_roast(roast_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Roast not found or expired.")

    score = row["overall_score"]
    band = row["band"]
    verdict = row["one_line_verdict"]
    title = get_credential_title(score, band, seed=roast_id)

    pdf_path = generate_certificate_pdf(
        roast_id=roast_id,
        candidate_name="Candidate",
        score=score,
        band=band,
        one_line_verdict=verdict,
        created_at=str(row.get("created_at", "")),
    )

    return JSONResponse(
        content={
            "status": "success",
            "roast_id": roast_id,
            "credential_title": title,
            "download_url": f"/api/roast/{roast_id}/certificate/download",
        }
    )


@router.get("/roast/{roast_id}/certificate/download")
async def download_certificate(roast_id: str, request: Request) -> FileResponse:
    lang = language_from_request(request)
    if roast_id in ("demo", "demo-roast", "sample-roast-1"):
        row = SAMPLE_ROAST_RESPONSE if lang == "hi-IN" else ENGLISH_SAMPLE_ROAST_RESPONSE
    else:
        row = database.get_roast(roast_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Roast not found or expired.")

    pdf_path = generate_certificate_pdf(
        roast_id=roast_id,
        candidate_name="Candidate",
        score=row["overall_score"],
        band=row["band"],
        one_line_verdict=row["one_line_verdict"],
        created_at=str(row.get("created_at", "")),
        language=lang,
    )

    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=500, detail="Failed to render certificate PDF.")

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"ResumeRoast-Certificate-{roast_id[:8]}.pdf",
        headers={"Content-Disposition": f'attachment; filename="ResumeRoast-Certificate-{roast_id[:8]}.pdf"'},
    )


class ReactionPayload(BaseModel):
    emoji: str


@router.get("/roast/{roast_id}/reactions")
async def get_reactions(roast_id: str) -> JSONResponse:
    reactions = database.get_roast_reactions(roast_id)
    return JSONResponse(content={"roast_id": roast_id, "reactions": reactions})


_REACTION_COUNTS_BY_CLIENT: dict[str, int] = {}
MAX_REACTIONS_PER_CLIENT_PER_ROAST = 10


@router.post("/roast/{roast_id}/react")
async def add_reaction(roast_id: str, payload: ReactionPayload, request: Request) -> JSONResponse:
    client_key = f"{_device_fingerprint(request)}:{roast_id}"
    if len(_REACTION_COUNTS_BY_CLIENT) > 5000:
        _REACTION_COUNTS_BY_CLIENT.clear()
    current_count = _REACTION_COUNTS_BY_CLIENT.get(client_key, 0)
    if current_count >= MAX_REACTIONS_PER_CLIENT_PER_ROAST:
        # Rate-limit reached; return existing reactions without incrementing
        reactions = database.get_roast_reactions(roast_id)
        return JSONResponse(content={"roast_id": roast_id, "reactions": reactions, "limited": True})

    emoji = payload.emoji.strip().lower()
    if emoji not in database.VALID_REACTION_EMOJIS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid emoji. Must be one of: {sorted(list(database.VALID_REACTION_EMOJIS))}",
        )
    _REACTION_COUNTS_BY_CLIENT[client_key] = current_count + 1
    reactions = database.add_roast_reaction(roast_id, emoji)
    return JSONResponse(content={"roast_id": roast_id, "reactions": reactions})


class ComebackRequest(BaseModel):
    message: str
    history: list[dict] = []


@router.post("/roast/{roast_id}/comeback")
async def roast_comeback(roast_id: str, payload: ComebackRequest, request: Request) -> JSONResponse:
    """Generate in-character witty comeback when user argues back with the roast."""
    user_msg = payload.message.strip()
    if not user_msg:
        raise HTTPException(status_code=422, detail="Message cannot be empty.")

    roast = database.get_roast(roast_id)
    if not roast:
        if roast_id != "demo":
            raise HTTPException(status_code=404, detail="Roast not found or expired.")
        lang = language_from_request(request)
        roast = SAMPLE_ROAST_RESPONSE if lang == "hi-IN" else ENGLISH_SAMPLE_ROAST_RESPONSE

    lang = language_from_request(request)
    reply = ai_analyzer.generate_roast_comeback(
        roast=roast,
        user_msg=user_msg,
        lang=lang,
        history=payload.history,
    )
    return JSONResponse(content={"ok": True, "reply": reply})



