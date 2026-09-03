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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.db.database import init_db, cleanup_expired_roasts
from app.routers import battle, payment, roast, usage, voice, wall

# ---------------------------------------------------------------------------
# Rate limiter (per-IP, using slowapi)
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Resume Roast API",
    description="Brutally honest AI-powered resume critiques with WhatsApp voice notes, battles, and wall.",
    version="0.2.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
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


from fastapi import FastAPI, HTTPException, Request
from starlette.exceptions import HTTPException as StarletteHTTPException

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
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    cleanup_expired_roasts()


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
async def health() -> dict:
    return {"status": "ok", "service": "resume-roast-api"}

