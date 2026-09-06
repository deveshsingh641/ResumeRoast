"""
Match Router — Endpoints for Job Description (JD) Match Mode & ATS Reality Check.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db import database
from app.i18n.mapping import DEFAULT_LANGUAGE, language_from_request
from app.services import extractor
from app.services.jd_match_service import SAMPLE_JDS, analyze_jd_match

logger = logging.getLogger("match")
router = APIRouter(prefix="/api", tags=["match"])


class MatchJsonRequest(BaseModel):
    job_description: str
    resume_text: Optional[str] = None
    roast_id: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    language: Optional[str] = None


@router.get("/match/samples")
async def get_sample_jds() -> JSONResponse:
    """
    Return curated sample job descriptions for instant 1-click testing.
    """
    return JSONResponse(
        content={
            "status": "ok",
            "samples": SAMPLE_JDS,
        }
    )


@router.post("/match")
async def match_resume_with_jd(
    request: Request,
    file: Optional[UploadFile] = File(None),
    job_description: Optional[str] = Form(None),
    job_title: Optional[str] = Form(None),
    company_name: Optional[str] = Form(None),
    roast_id: Optional[str] = Form(None),
    resume_text: Optional[str] = Form(None),
    language: Optional[str] = Form(None),
) -> JSONResponse:
    """
    Compare resume against target job description.
    Supports either file upload (PDF/DOCX) or existing resume_text / roast_id.
    """
    # 1. Resolve content from JSON body if multipart is empty
    if not file and not job_description:
        try:
            body_json = await request.json()
            job_description = body_json.get("job_description")
            resume_text = body_json.get("resume_text")
            roast_id = body_json.get("roast_id")
            job_title = body_json.get("job_title")
            company_name = body_json.get("company_name")
            language = body_json.get("language")
        except Exception:
            pass

    if not job_description or len(job_description.strip()) < 30:
        raise HTTPException(
            status_code=422,
            detail="Please provide a valid Job Description with at least 30 characters.",
        )

    # 2. Extract or retrieve resume text
    extracted_text = ""
    if file:
        file_bytes = await file.read()
        if len(file_bytes) == 0:
            raise HTTPException(status_code=422, detail="Uploaded file is empty.")
        if len(file_bytes) > 5 * 1024 * 1024:
            raise HTTPException(status_code=422, detail="File size exceeds 5MB limit.")

        content_type = file.content_type or "application/octet-stream"
        try:
            extracted_text, _ = extractor.extract_text(file.filename or "resume.pdf", content_type, file_bytes)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail="Could not read uploaded document.")
    elif roast_id:
        existing_roast = database.get_roast(roast_id)
        if existing_roast and existing_roast.get("resume_text"):
            extracted_text = existing_roast["resume_text"]
        elif existing_roast:
            # Reconstruct from quoted issues if raw text not stored
            issues = existing_roast.get("issues") or []
            if isinstance(issues, str):
                import json as _json
                try:
                    issues = _json.loads(issues)
                except Exception:
                    issues = []
            extracted_text = "\n".join([iss.get("quoted_text", "") for iss in issues if isinstance(iss, dict)])

    if not extracted_text and resume_text:
        extracted_text = resume_text.strip()

    if not extracted_text or len(extracted_text.strip()) < 30:
        raise HTTPException(
            status_code=422,
            detail="Please upload a resume (PDF/DOCX) or provide an existing roast ID to match.",
        )

    # 3. Determine language
    lang = language or language_from_request(request)

    # 4. Determine user tier (Free vs Pro)
    user_email = request.headers.get("x-user-email") or request.cookies.get("user_email")
    is_pro = False
    if user_email:
        sub_status = database.get_user_subscription(user_email)
        is_pro = sub_status == "pro"

    # 5. Run AI Match analysis
    try:
        match_result = analyze_jd_match(
            resume_text=extracted_text,
            job_description=job_description.strip(),
            language=lang,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error in analyze_jd_match: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error analyzing job description match. Please try again in a moment.",
        )

    # 6. Apply Pro vs Free truncation
    all_missing = match_result.get("missing_keywords", [])
    all_rewrites = match_result.get("tailored_bullet_rewrites", [])

    is_truncated = not is_pro and (len(all_missing) > 2 or len(all_rewrites) > 1)
    visible_missing = all_missing if is_pro else all_missing[:2]
    visible_rewrites = all_rewrites if is_pro else all_rewrites[:1]

    return JSONResponse(
        content={
            "status": "success",
            "match_score": match_result["match_score"],
            "ats_status": match_result["ats_status"],
            "verdict": match_result["verdict"],
            "job_title": job_title or "Target Role",
            "company_name": company_name or "Target Company",
            "matched_skills": match_result.get("matched_skills", []),
            "missing_keywords": visible_missing,
            "total_missing_keywords": len(all_missing),
            "irrelevant_clutter": match_result.get("irrelevant_clutter", []),
            "tailored_bullet_rewrites": visible_rewrites,
            "total_tailored_rewrites": len(all_rewrites),
            "is_truncated": is_truncated,
            "is_pro": is_pro,
        }
    )
