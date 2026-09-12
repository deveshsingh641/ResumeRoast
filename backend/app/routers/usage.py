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
from app.services.pro_auth import get_authenticated_pro_email

router = APIRouter(prefix="/api", tags=["usage"])

FREE_TIER_LIMIT = int(os.getenv("FREE_TIER_DAILY_LIMIT", "1"))


def _device_fingerprint(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
    ua = request.headers.get("User-Agent", "standard-browser")
    custom_fp = (request.headers.get("X-Device-Fingerprint") or "").strip()
    raw = f"{ip}:{ua}:{custom_fp}" if custom_fp else f"{ip}:{ua}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


@router.get("/usage")
async def get_usage(request: Request, email: Optional[str] = None) -> JSONResponse:
    auth_pro_email = get_authenticated_pro_email(request)
    is_pro = False
    if auth_pro_email:
        clean_email = auth_pro_email.strip().lower()
        sub_status = database.get_user_subscription(clean_email)
        if sub_status == "pro":
            is_pro = True

    forwarded = request.headers.get("X-Forwarded-For")
    client_ip = forwarded.split(",")[0].strip() if forwarded else (request.client.host if request.client else "127.0.0.1")
    fingerprint = _device_fingerprint(request)

    used = max(database.get_usage_count(fingerprint), database.get_usage_count(f"ip:{client_ip}"))
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
