"""
Usage router — returns current user's remaining free roasts today.
"""
from __future__ import annotations

import hashlib
import os

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
async def get_usage(request: Request) -> JSONResponse:
    fingerprint = _device_fingerprint(request)
    used = database.get_usage_count(fingerprint)
    remaining = max(0, FREE_TIER_LIMIT - used)

    return JSONResponse(
        content={
            "used": used,
            "remaining": remaining,
            "limit": FREE_TIER_LIMIT,
            "is_pro": False,  # TODO: check subscription_status when auth is added
        }
    )
