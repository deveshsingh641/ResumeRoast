"""
Cryptographic Pro Entitlement & Ownership Authentication Service.
Prevents unauthenticated Pro spoofing via self-asserted emails or headers.
Issues and validates HMAC-SHA256 signed bearer tokens upon verified payment.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Optional

from fastapi import Request

logger = logging.getLogger("security.pro_auth")

def _get_signing_key() -> bytes:
    """
    Retrieve secret key for signing entitlement tokens.
    Strictly requires TOKEN_SECRET_KEY to prevent fallback to known or reused keys.
    """
    key = os.getenv("TOKEN_SECRET_KEY", "").strip()
    if not key:
        raise RuntimeError("TOKEN_SECRET_KEY must be configured in environment for Pro entitlement tokens.")
    return key.encode("utf-8")


def create_pro_token(email: str, expires_in_days: int = 30) -> str:
    """Generate a tamper-proof HMAC-SHA256 signed Pro token for a paying user."""
    clean_email = email.strip().lower()
    payload = {
        "email": clean_email,
        "is_pro": True,
        "iat": int(time.time()),
        "exp": int(time.time()) + (expires_in_days * 86400),
    }
    raw_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(raw_json).decode("ascii").rstrip("=")
    
    signature = hmac.new(
        _get_signing_key(),
        b64_payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    
    return f"{b64_payload}.{signature}"


def verify_pro_token(token: Optional[str]) -> Optional[str]:
    """
    Validate HMAC-SHA256 signature and expiration of a Pro token.
    Returns verified email if valid, or None if missing/invalid/expired.
    """
    if not token or "." not in token:
        return None

    try:
        b64_payload, signature = token.strip().split(".", 1)
        expected_sig = hmac.new(
            _get_signing_key(),
            b64_payload.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, signature):
            logger.warning("Tampered or invalid Pro token signature presented.")
            return None

        # Restore base64 padding
        padding = 4 - (len(b64_payload) % 4)
        if padding != 4:
            b64_payload += "=" * padding

        payload_bytes = base64.urlsafe_b64decode(b64_payload.encode("ascii"))
        data = json.loads(payload_bytes.decode("utf-8"))

        if data.get("exp") and data["exp"] < time.time():
            logger.info(f"Expired Pro token presented for {data.get('email')}")
            return None

        return str(data.get("email", "")).strip().lower() or None
    except Exception as e:
        logger.warning(f"Error parsing Pro token: {e}")
        return None


def get_authenticated_pro_email(request: Request) -> Optional[str]:
    """
    Extract and cryptographically verify Pro user identity from request.
    Checks:
    1. X-Pro-Token header
    2. Authorization: Bearer <token>
    3. Cookie: resumeroast_pro_token
    """
    token = request.headers.get("X-Pro-Token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
    if not token:
        token = request.cookies.get("resumeroast_pro_token")

    return verify_pro_token(token)
