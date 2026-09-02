"""
Roast router — handles resume upload, text extraction, deduplication, AI analysis, and retrieval.
"""
from __future__ import annotations

import hashlib
import os
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.db import database
from app.services import ai_analyzer, extractor

router = APIRouter(prefix="/api", tags=["roast"])

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
FREE_TIER_LIMIT = int(os.getenv("FREE_TIER_DAILY_LIMIT", "1"))


def _device_fingerprint(request: Request) -> str:
    """
    Generate a semi-stable anonymous fingerprint from IP + User-Agent.
    Gracefully falls back to client host if forwarded headers are absent.
    """
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

    # 2. Rate-limit check (server-enforced)
    fingerprint = _device_fingerprint(request)
    usage_count = database.get_usage_count(fingerprint)

    is_free_tier = True  # TODO: Check subscription when authenticated
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

    # 3. Deduplication check (avoid double processing on rapid double-clicks)
    content_hash = hashlib.sha256(file_bytes).hexdigest()
    existing_roast_id = database.check_dedup(content_hash)
    if existing_roast_id:
        existing_roast = database.get_roast(existing_roast_id)
        if existing_roast:
            import json as _json
            issues = existing_roast["issues"]
            if isinstance(issues, str):
                issues = _json.loads(issues)
            strengths = existing_roast["strengths"]
            if isinstance(strengths, str):
                strengths = _json.loads(strengths)

            return JSONResponse(
                content={
                    "id": existing_roast_id,
                    "overall_score": existing_roast["overall_score"],
                    "band": existing_roast["band"],
                    "one_line_verdict": existing_roast["one_line_verdict"],
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
        analysis = ai_analyzer.analyze_resume(resume_text)
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


@router.get("/roast/{roast_id}")
async def get_roast(roast_id: str, request: Request) -> JSONResponse:
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

    is_truncated = len(issues) > 3
    visible_issues = issues[:3]

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
