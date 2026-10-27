"""
Authentication & User Session Router for Resume Roast.
Allows users to sign in with their email address to synchronize their Pro subscription,
unlimited daily roasts, and features across devices and browsers.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.limiter import limiter
from app.db import database
from app.services.pro_auth import create_pro_token, get_authenticated_pro_email

logger = logging.getLogger("auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class LoginRequest(BaseModel):
    email: str


@router.post("/login")
@limiter.limit("15/minute")
async def email_login(payload: LoginRequest, request: Request) -> JSONResponse:
    """
    Passwordless instant email sign-in / restore endpoint.
    If the email has purchased a Pro subscription in the database,
    this endpoint cryptographically signs and returns a Pro token,
    instantly activating Pro on the client device.
    """
    clean_email = payload.email.strip().lower()
    if not clean_email or not EMAIL_REGEX.match(clean_email):
        raise HTTPException(
            status_code=422,
            detail="Please provide a valid email address (e.g. name@gmail.com).",
        )

    # Ensure user record exists in database
    database.create_or_get_user(clean_email)
    sub_status = database.get_user_subscription(clean_email)
    is_pro = (sub_status == "pro")

    pro_token = None
    if is_pro:
        pro_token = create_pro_token(clean_email, expires_in_days=30)
        logger.info(f"User {clean_email} logged in with active Pro entitlement.")
    else:
        logger.info(f"User {clean_email} logged in on Free tier.")

    response = JSONResponse(
        content={
            "ok": True,
            "email": clean_email,
            "is_pro": is_pro,
            "subscription_status": sub_status,
            "token": pro_token,
            "message": (
                f"Welcome back! Pro VIP subscription is active for {clean_email}."
                if is_pro
                else f"Signed in as {clean_email} (Free Tier)."
            ),
        }
    )

    if pro_token:
        response.set_cookie(
            key="resumeroast_pro_token",
            value=pro_token,
            max_age=30 * 86400,
            httponly=True,
            samesite="lax",
        )
    return response


@router.get("/me")
async def get_current_user(request: Request) -> JSONResponse:
    """
    Return current session details and Pro entitlement status.
    """
    auth_email = get_authenticated_pro_email(request)
    user_email = (
        auth_email
        or (request.headers.get("X-User-Email") or "").strip().lower()
        or None
    )

    if not user_email:
        return JSONResponse(
            content={
                "authenticated": False,
                "email": None,
                "is_pro": False,
                "subscription_status": "guest",
            }
        )

    sub_status = database.get_user_subscription(user_email)
    is_pro = (sub_status == "pro" and bool(auth_email))

    return JSONResponse(
        content={
            "authenticated": True,
            "email": user_email,
            "is_pro": is_pro,
            "subscription_status": sub_status,
        }
    )


@router.post("/logout")
async def logout() -> JSONResponse:
    """Clear session cookie on server."""
    response = JSONResponse(
        content={
            "ok": True,
            "message": "Logged out successfully.",
        }
    )
    response.delete_cookie("resumeroast_pro_token")
    return response
