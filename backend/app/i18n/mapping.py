"""
Country → language lookup table.

Adding a third language later is a data change here (plus a new prompt module
and locale JSON), not scattered if/else across the app.
"""
from __future__ import annotations

from typing import Any, Optional

# Canonical language codes used by API, DB, and AI prompt registry.
DEFAULT_LANGUAGE = "en"
HINGLISH_LANGUAGE = "hi-IN"

SUPPORTED_LANGUAGES: frozenset[str] = frozenset({DEFAULT_LANGUAGE, HINGLISH_LANGUAGE})

# ISO 3166-1 alpha-2 country code → language code.
# Unlisted countries fall through to DEFAULT_LANGUAGE.
COUNTRY_TO_LANGUAGE: dict[str, str] = {
    "IN": HINGLISH_LANGUAGE,
}

# Cloudflare / geo providers use these when country cannot be determined.
_UNKNOWN_COUNTRY_CODES = frozenset({"", "XX", "T1", "A1", "A2", "O1"})

_ALIASES: dict[str, str] = {
    "hi": HINGLISH_LANGUAGE,
    "hi-in": HINGLISH_LANGUAGE,
    "hi_IN": HINGLISH_LANGUAGE,
    "en-us": DEFAULT_LANGUAGE,
    "en-gb": DEFAULT_LANGUAGE,
    "en-IN": DEFAULT_LANGUAGE,
    "en_US": DEFAULT_LANGUAGE,
}


def normalize_language(code: Optional[str]) -> str:
    """Return a supported language code; unknown or empty → English."""
    if not code or not str(code).strip():
        return DEFAULT_LANGUAGE
    raw = str(code).strip()
    if raw in SUPPORTED_LANGUAGES:
        return raw
    aliased = _ALIASES.get(raw) or _ALIASES.get(raw.replace("_", "-"))
    if aliased:
        return aliased
    lower = raw.lower()
    if lower in ("en", "eng", "english"):
        return DEFAULT_LANGUAGE
    if lower.startswith("hi"):
        return HINGLISH_LANGUAGE
    return DEFAULT_LANGUAGE


def language_from_country(country_code: Optional[str]) -> str:
    """
    Map a country code to a language.

    Failed / unknown detection (VPN, Cloudflare XX, missing header) silently
    falls back to English — never raises.
    """
    if not country_code:
        return DEFAULT_LANGUAGE
    code = str(country_code).strip().upper()
    if code in _UNKNOWN_COUNTRY_CODES:
        return DEFAULT_LANGUAGE
    return COUNTRY_TO_LANGUAGE.get(code, DEFAULT_LANGUAGE)


def language_from_request(request: Any) -> str:
    """
    Resolve language from an explicit client override (header or query).

    Does not geolocate. Geo is first-visit only on the frontend; subsequent
    requests send X-Language. Invalid values fall back to English.
    """
    try:
        header = request.headers.get("X-Language") or request.headers.get("X-Preferred-Language")
    except Exception:
        header = None
    try:
        query = request.query_params.get("lang") or request.query_params.get("language")
    except Exception:
        query = None
    return normalize_language(header or query)
