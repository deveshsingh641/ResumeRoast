"""
Suggestion Box Router — Low-friction, responsive feedback and feature ideas.
Includes honeypot bot defense, per-IP rate limiting, and admin review triage.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.db import database
from app.services.email_notifier import send_suggestion_alert

logger = logging.getLogger("suggestion")
router = APIRouter(tags=["suggestions"])


def _device_fingerprint(request: Request) -> str:
    """Generate anonymous 32-char SHA-256 fingerprint from IP and User-Agent."""
    x_forwarded = request.headers.get("X-Forwarded-For")
    if x_forwarded:
        ip = x_forwarded.split(",")[0].strip()
    elif request.client and request.client.host:
        ip = request.client.host
    else:
        ip = "127.0.0.1"
    ua = request.headers.get("User-Agent", "")
    raw = f"{ip}:{ua}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _verify_admin_access(request: Request) -> bool:
    """Verify admin secret key from X-Admin-Key header or query parameter."""
    configured_key = os.getenv("ADMIN_SECRET_KEY", "").strip()
    provided_key = (
        request.headers.get("X-Admin-Key")
        or request.query_params.get("admin_key")
        or ""
    ).strip()
    if not configured_key:
        return True
    return hmac.compare_digest(configured_key, provided_key)


class SuggestionCreateRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=2000)
    category: Optional[str] = "feedback"  # "feature" | "bug" | "feedback" | "other"
    email: Optional[str] = None
    website: Optional[str] = None  # Honeypot field (bots fill this, real users never do)


class SuggestionStatusUpdateRequest(BaseModel):
    status: str  # "new" | "reviewed" | "planned" | "done" | "not-planned"


@router.post("/api/suggestions")
async def create_suggestion(
    payload: SuggestionCreateRequest,
    request: Request,
    background_tasks: BackgroundTasks,
) -> JSONResponse:
    """
    Public low-friction suggestion & feedback box.
    No auth required. Includes honeypot, daily rate limiting, and background email alerts.
    """
    # 1. Honeypot check: real users never fill the hidden 'website' field
    if payload.website and payload.website.strip():
        logger.info("[HONEYPOT] Bot submission caught and silently dropped.")
        return JSONResponse(
            content={
                "ok": True,
                "message": "Got it, thanks! 🙌 We actually read these.",
            }
        )

    # 2. Rate limiting (max 10 suggestions per day per IP/fingerprint)
    fingerprint = _device_fingerprint(request)
    usage_key = f"suggestions:{fingerprint}"
    daily_count = database.get_usage_count(usage_key)
    if daily_count >= 10:
        raise HTTPException(
            status_code=429,
            detail="You have submitted several ideas today! Please take a breather and submit more tomorrow.",
        )

    # 3. Clean and validate
    clean_text = payload.text.strip()
    if len(clean_text) < 3:
        raise HTTPException(status_code=400, detail="Suggestion text is too short.")

    clean_email = payload.email.strip() if payload.email else None
    if clean_email and ("@" not in clean_email or len(clean_email) > 150):
        clean_email = None

    category = (payload.category or "feedback").lower().strip()
    if category not in {"feature", "bug", "feedback", "other"}:
        category = "feedback"

    # 4. Save to database
    entry = database.save_suggestion(
        text=clean_text,
        category=category,
        email=clean_email,
        device_fingerprint=fingerprint,
    )

    # 5. Increment usage counter
    database.increment_usage(usage_key)

    # 6. Trigger non-blocking background email dispatch to founder
    background_tasks.add_task(
        send_suggestion_alert,
        suggestion_id=entry["id"],
        text=clean_text,
        category=category,
        submitter_email=clean_email,
        created_at=entry.get("created_at"),
    )

    logger.info(f"[SUGGESTION] New suggestion received #{entry['id']} [{category}]: {clean_text[:60]!r}")

    return JSONResponse(
        content={
            "ok": True,
            "id": entry["id"],
            "message": "Got it, thanks! 🙌 We actually read these.",
        }
    )


@router.get("/api/admin/suggestions")
async def get_admin_suggestions(
    request: Request,
    limit: int = 50,
    status: Optional[str] = None,
) -> JSONResponse:
    """Admin-only list of submitted suggestions sorted newest first."""
    if not _verify_admin_access(request):
        raise HTTPException(status_code=401, detail="Unauthorized admin access")

    suggestions = database.get_suggestions(limit=min(max(limit, 1), 200), status=status)
    total_count = database.get_suggestion_count()

    return JSONResponse(
        content={
            "ok": True,
            "count": len(suggestions),
            "total": total_count,
            "suggestions": suggestions,
        }
    )


@router.patch("/api/admin/suggestions/{suggestion_id}")
async def update_admin_suggestion_status(
    suggestion_id: str,
    payload: SuggestionStatusUpdateRequest,
    request: Request,
) -> JSONResponse:
    """Admin-only status updater ('new' | 'reviewed' | 'planned' | 'done' | 'not-planned')."""
    if not _verify_admin_access(request):
        raise HTTPException(status_code=401, detail="Unauthorized admin access")

    valid_statuses = {"new", "reviewed", "planned", "done", "not-planned"}
    clean_status = payload.status.strip().lower()
    if clean_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{payload.status}'. Must be one of: {', '.join(valid_statuses)}",
        )

    success = database.update_suggestion_status(suggestion_id, clean_status)
    if not success:
        raise HTTPException(status_code=404, detail="Suggestion not found or could not be updated")

    return JSONResponse(
        content={
            "ok": True,
            "id": suggestion_id,
            "status": clean_status,
            "message": f"Suggestion status successfully updated to '{clean_status}'.",
        }
    )
