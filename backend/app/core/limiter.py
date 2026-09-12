"""
Shared Rate Limiter for Resume Roast.
Extracts client IP safely with reverse-proxy awareness (X-Forwarded-For).
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
