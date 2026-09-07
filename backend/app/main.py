"""
FastAPI application entry point.
"""
from __future__ import annotations

import logging
import os

from dotenv import load_dotenv

load_dotenv()

# Configure root logger with informative timestamp format
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.db.database import init_db, cleanup_expired_roasts
from app.routers import analytics, battle, i18n, match, payment, roast, suggestion, usage, voice, waitlist, wall

from datetime import datetime, timezone
from contextlib import asynccontextmanager

# ---------------------------------------------------------------------------
# Rate limiter (per-IP, using slowapi)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)


def validate_startup_environment() -> None:
    """
    Validates essential environment variables on boot to prevent delayed runtime failures.
    Fails fast with actionable messages naming precisely what is missing.
    """
    env = os.getenv("ENVIRONMENT", "development").lower()
    is_prod = env == "production"

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    if not (gemini_key or groq_key or anthropic_key):
        warning_msg = (
            "CRITICAL STARTUP CONFIGURATION WARNING: No AI provider API key found! "
            "Please configure at least one of: GEMINI_API_KEY, GROQ_API_KEY, or ANTHROPIC_API_KEY."
        )
        logger.warning(warning_msg)
        if is_prod:
            raise RuntimeError(warning_msg)
    else:
        active_providers = []
        if gemini_key:
            active_providers.append("Gemini")
        if groq_key:
            active_providers.append("Groq")
        if anthropic_key:
            active_providers.append("Anthropic")
        logger.info(f"AI Providers active: {', '.join(active_providers)}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_startup_environment()
    try:
        init_db()
    except Exception as e:
        logger.warning(f"Database init warning: {e}")
    try:
        cleanup_expired_roasts()
    except Exception as e:
        logger.warning(f"Database cleanup warning: {e}")
    yield


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Resume Roast API",
    description="Brutally honest AI-powered resume critiques with WhatsApp voice notes, battles, and wall.",
    version="0.2.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    lifespan=lifespan,
)

# Attach slowapi rate-limit exceeded handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ---------------------------------------------------------------------------
# CORS (Strict origin list without wildcard to comply with credentials spec)
# ---------------------------------------------------------------------------
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
configured_origins = [
    url.strip().rstrip("/")
    for url in FRONTEND_URL.split(",")
    if url.strip() and url.strip() != "*"
]
dev_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
origins = list(dict.fromkeys(configured_origins + dev_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(roast.router)
app.include_router(voice.router)
app.include_router(battle.router)
app.include_router(wall.router)
app.include_router(usage.router)
app.include_router(payment.router)
app.include_router(analytics.router)
app.include_router(i18n.router)
app.include_router(waitlist.router)
app.include_router(match.router)
app.include_router(suggestion.router)

# ---------------------------------------------------------------------------
# Global error handler — preserves HTTPExceptions, never leaks raw stack traces
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=getattr(exc, "headers", None),
        )
    logger.exception(f"Unhandled internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Something went wrong on our end. Please try again in a moment."
        },
    )


# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


# ---------------------------------------------------------------------------
# Health & Root check
# ---------------------------------------------------------------------------
@app.get("/")
async def root() -> dict:
    return {
        "status": "ok",
        "service": "resume-roast-api",
        "message": "Resume Roast Backend is live and running 🔥",
    }


@app.get("/health")
@app.get("/api/health")
async def health() -> dict:
    db_status = "in-memory"
    if database.DATABASE_URL:
        try:
            with database._get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
            db_status = "connected"
        except Exception:
            db_status = "disconnected"

    return {
        "status": "ok" if db_status != "disconnected" else "degraded",
        "service": "resume-roast-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": db_status,
        "ai_status": "ready",
        "version": "0.2.0",
    }

