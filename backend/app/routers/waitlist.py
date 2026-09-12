"""
Pro Waitlist Router — Captures interested users while payment gateway is in pre-launch / KYC review.
Supports frictionless email capture, deduplication, user_id linking, and source tracking.
"""


import logging
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.limiter import limiter
from app.db import database

logger = logging.getLogger("waitlist")
router = APIRouter(prefix="/api", tags=["waitlist"])

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)+$")


class WaitlistJoinRequest(BaseModel):
    email: str
    source: Optional[str] = "pricing"
    user_id: Optional[str] = None


@router.post("/waitlist/join")
@router.post("/v1/waitlist/join")
@limiter.limit("15/minute")
async def join_waitlist(payload: WaitlistJoinRequest, request: Request) -> JSONResponse:
    """
    Add a user's email to the Pro early-access waitlist.
    Deduplicates gracefully without throwing an error if already subscribed.
    """
    clean_email = payload.email.strip().lower()

    if not clean_email or not EMAIL_REGEX.match(clean_email):
        raise HTTPException(
            status_code=422,
            detail="Please provide a valid email address.",
        )

    clean_source = (payload.source or "pricing").strip()[:100]

    try:
        record, is_new = database.add_to_waitlist(
            email=clean_email,
            source=clean_source,
            user_id=payload.user_id,
        )

        if is_new:
            logger.info(f"New Pro waitlist signup: {clean_email} (source: {clean_source})")
            return JSONResponse(
                content={
                    "status": "joined",
                    "message": "You're on the list — we'll email you the second Pro is live 🎉",
                    "is_already_on_list": False,
                    "email": clean_email,
                    "source": clean_source,
                }
            )
        else:
            logger.info(f"Duplicate waitlist submission acknowledged for: {clean_email}")
            return JSONResponse(
                content={
                    "status": "already_joined",
                    "message": "You're already on the list! We'll email you the second Pro is live 🎉",
                    "is_already_on_list": True,
                    "email": clean_email,
                    "source": clean_source,
                }
            )
    except Exception as e:
        logger.error(f"Error saving waitlist entry for {clean_email}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to record waitlist entry. Please try again in a moment.",
        )


@router.get("/waitlist/stats")
async def waitlist_stats() -> JSONResponse:
    """
    Internal diagnostic count of waitlist participants.
    """
    total = database.get_waitlist_count()
    return JSONResponse(
        content={
            "status": "ok",
            "total_waitlist": total,
        }
    )


@router.get("/waitlist/entries")
async def waitlist_entries(limit: int = 100) -> JSONResponse:
    """
    Internal diagnostic view of recent waitlist participants (masked emails for privacy).
    """
    entries = database.get_waitlist_entries(limit=min(limit, 200))
    masked_entries = []
    for entry in entries:
        em = entry.get("email", "")
        parts = em.split("@")
        masked_email = f"{parts[0][:3]}***@{parts[1]}" if len(parts) == 2 and len(parts[0]) > 3 else em
        masked_entries.append({
            "id": entry.get("id"),
            "email_masked": masked_email,
            "source": entry.get("source"),
            "user_id": entry.get("user_id"),
            "created_at": entry.get("created_at"),
        })
    return JSONResponse(
        content={
            "total": len(masked_entries),
            "entries": masked_entries,
        }
    )
