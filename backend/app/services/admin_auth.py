"""
Hardened Founder Authentication and Brute-Force Defense Service.
Protects confidential founder dashboards, candidate resumes, user suggestions, and billing overrides.
"""
from __future__ import annotations

import hmac
import logging
import os
import time
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, Request

logger = logging.getLogger("security.admin_auth")

# Brute-force tracking: client_ip -> list of failed attempt timestamps (epoch seconds)
_failed_attempts: dict[str, list[float]] = defaultdict(list)
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_WINDOW_SECONDS = 900  # 15 minutes


def _get_client_ip(request: Request) -> str:
    """Extract client IP with proxy awareness."""
    x_forwarded = request.headers.get("X-Forwarded-For")
    if x_forwarded:
        return x_forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


def verify_admin_access(request: Request, explicit_key: Optional[str] = None) -> bool:
    """
    Verify founder access with:
    1. Brute-force rate limiting and automatic IP lockout.
    2. Constant-time HMAC comparison (timing attack defense).
    3. Cookie, Header, Query Parameter, or explicit key validation.
    4. Full security audit logging.
    """
    configured_key = os.getenv("ADMIN_SECRET_KEY", "").strip()

    # In isolated testing environments where no key is configured, permit access
    if not configured_key:
        return True

    client_ip = _get_client_ip(request)
    now = time.time()

    # Clean expired failed attempt timestamps outside the 15-minute lockout window
    _failed_attempts[client_ip] = [
        t for t in _failed_attempts[client_ip] if now - t < LOCKOUT_WINDOW_SECONDS
    ]

    # Check if IP is currently locked out
    if len(_failed_attempts[client_ip]) >= MAX_FAILED_ATTEMPTS:
        logger.warning(
            f"[SECURITY_LOCKOUT] IP {client_ip} is locked out from founder dashboard due to {len(_failed_attempts[client_ip])} failed attempts."
        )
        raise HTTPException(
            status_code=429,
            detail="Security lockout: Too many failed founder authentication attempts. Access locked for 15 minutes.",
        )

    # Check incoming credentials across explicit_key, cookie, header, and query parameter
    provided_key = (
        explicit_key
        or request.cookies.get("rr_admin_key")
        or request.headers.get("X-Admin-Key")
        or request.query_params.get("admin_key")
        or request.query_params.get("key")
        or ""
    ).strip()

    if not provided_key:
        return False

    # Constant-time comparison to prevent side-channel timing attacks
    is_valid = hmac.compare_digest(configured_key, provided_key)

    if not is_valid:
        _failed_attempts[client_ip].append(now)
        failures_count = len(_failed_attempts[client_ip])
        remaining = max(0, MAX_FAILED_ATTEMPTS - failures_count)
        logger.warning(
            f"[SECURITY_ALERT] Invalid founder key attempt #{failures_count} from IP {client_ip}. Remaining attempts before lockout: {remaining}"
        )
        return False

    # Valid authentication: clear any prior failed attempts for this IP
    if client_ip in _failed_attempts:
        del _failed_attempts[client_ip]

    logger.info(f"[FOUNDER_ACCESS_GRANTED] Founder authenticated successfully from IP {client_ip}")
    return True


def apply_secure_admin_headers(response):
    """Ensure confidential admin data is never cached by intermediate proxies or browser cache."""
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response
