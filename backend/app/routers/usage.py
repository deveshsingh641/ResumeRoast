"""
Usage router — returns current user's remaining free roasts today.
"""
from __future__ import annotations

import hashlib
import os

from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.db import database

router = APIRouter(prefix="/api", tags=["usage"])

FREE_TIER_LIMIT = int(os.getenv("FREE_TIER_DAILY_LIMIT", "1"))


def _device_fingerprint(request: Request) -> str:
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")
    ua = request.headers.get("User-Agent", "")
    return hashlib.sha256(f"{ip}:{ua}".encode()).hexdigest()[:32]


@router.get("/usage")
async def get_usage(request: Request, email: Optional[str] = None) -> JSONResponse:
    user_email = email or request.headers.get("X-User-Email")
    is_pro = False
    if user_email:
        clean_email = user_email.strip().lower()
        is_pro = (database.get_user_subscription(clean_email) == "pro")

    fingerprint = _device_fingerprint(request)
    used = database.get_usage_count(fingerprint)
    remaining = 999999 if is_pro else max(0, FREE_TIER_LIMIT - used)
    limit = 999999 if is_pro else FREE_TIER_LIMIT

    return JSONResponse(
        content={
            "used": used,
            "remaining": remaining,
            "limit": limit,
            "is_pro": is_pro,
        }
    )
