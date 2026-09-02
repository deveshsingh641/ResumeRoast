"""
FastAPI application entry point.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

load_dotenv()

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
# CORS
# ---------------------------------------------------------------------------
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
origins = [url.strip().rstrip("/") for url in FRONTEND_URL.split(",") if url.strip()]
for default_origin in ["http://localhost:5173", "http://localhost:3000", "*"]:
    if default_origin not in origins:
        origins.append(default_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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


# ---------------------------------------------------------------------------
# Global error handler — never leak raw stack traces
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
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
# Health check
# ---------------------------------------------------------------------------
@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "resume-roast-api"}
