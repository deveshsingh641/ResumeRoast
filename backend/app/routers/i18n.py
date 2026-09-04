"""
Country-based language detection and user language preference endpoints.
Provides first-visit auto-detection via headers (CF-IPCountry, etc.)
and persistence of user preferences in the database.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db import database
from app.i18n.mapping import (
    DEFAULT_LANGUAGE,
    language_from_country,
    normalize_language,
)

logger = logging.getLogger("i18n")
router = APIRouter(tags=["i18n"])


class UserLanguageUpdate(BaseModel):
    email: str
    language: str


def _detect_country_from_request(request: Request) -> Optional[str]:
    """
    Extract 2-letter ISO country code from proxy headers or query override.
    Priority:
    1. Query param ?country= (useful for testing and previews)
    2. Cloudflare CF-IPCountry
    3. Vercel X-Vercel-IP-Country
    4. CloudFront CloudFront-Viewer-Country
    5. Generic X-Country-Code / X-Geo-Country
    """
    # 1. Query override (useful for testing)
    q_country = request.query_params.get("country")
    if q_country and len(q_country.strip()) == 2:
        return q_country.strip().upper()

    # 2. Cloudflare header
    cf = request.headers.get("CF-IPCountry")
    if cf and len(cf.strip()) == 2:
        return cf.strip().upper()

    # 3. Vercel header
    vercel = request.headers.get("X-Vercel-IP-Country")
    if vercel and len(vercel.strip()) == 2:
        return vercel.strip().upper()

    # 4. AWS CloudFront header
    cf_aws = request.headers.get("CloudFront-Viewer-Country")
    if cf_aws and len(cf_aws.strip()) == 2:
        return cf_aws.strip().upper()

    # 5. Generic proxy headers
    generic = request.headers.get("X-Country-Code") or request.headers.get("X-Geo-Country")
    if generic and len(generic.strip()) == 2:
        return generic.strip().upper()

    return None


@router.get("/api/i18n/detect")
async def detect_language(request: Request) -> JSONResponse:
    """
    Auto-detect country and recommend a default language for first-time visitors.
    Falls back silently to 'en' when detection is unavailable.
    """
    country = _detect_country_from_request(request)
    lang = language_from_country(country) if country else DEFAULT_LANGUAGE
    return JSONResponse(
        content={
            "country": country,
            "language": lang,
        }
    )


@router.post("/api/user/language")
async def set_user_language(payload: UserLanguageUpdate) -> JSONResponse:
    """Persist user's explicitly selected language in the database."""
    email = payload.email.strip().lower()
    if not email:
        return JSONResponse(
            status_code=400,
            content={"error": "email is required"},
        )
    normalized_lang = normalize_language(payload.language)
    database.update_user_language(email, normalized_lang)
    return JSONResponse(
        content={
            "ok": True,
            "email": email,
            "language": normalized_lang,
        }
    )


@router.get("/api/user/language")
async def get_user_language_endpoint(email: str) -> JSONResponse:
    """Fetch stored language preference for a given user email."""
    cleaned = email.strip().lower()
    stored = database.get_user_language(cleaned)
    return JSONResponse(
        content={
            "email": cleaned,
            "language": stored or DEFAULT_LANGUAGE,
        }
    )
