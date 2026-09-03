"""
Voice Note Roast Router — generates and serves WhatsApp-style Hinglish voice roasts.
"""
from __future__ import annotations

import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

from app.db import database
from app.services import voice_service

router = APIRouter(prefix="/api/roast", tags=["voice"])


DEMO_VOICE_ROAST = {
    "id": "demo",
    "overall_score": 28,
    "band": "weak",
    "one_line_verdict": "Bhai resume hai ya suspense novel? 🕵️",
    "issues": [
        {"quoted_text": "Responsible for building UI components", "category": "no-metrics", "roast": "Responsible for likhna band karo yaar recruiter ko number chahiye"},
        {"quoted_text": "DECLARATION: I hereby declare all information is true", "category": "formatting", "roast": "Bhai 2005 ka declaration kyu daal rakha hai"},
    ],
}


@router.post("/{roast_id}/voice")
async def generate_voice_roast(roast_id: str, request: Request) -> JSONResponse:
    """
    Generate or retrieve an existing WhatsApp-style voice note roast.
    Uses stored one_line_verdict and top issues to compose natural spoken script.
    """
    if roast_id in ("demo", "demo-roast", "sample-roast-1"):
        roast = DEMO_VOICE_ROAST
    else:
        roast = database.get_roast(roast_id)

    if not roast:
        raise HTTPException(
            status_code=404,
            detail="Roast not found or expired. Please upload your resume first.",
        )

    # Parse issues
    issues = roast.get("issues", [])
    if isinstance(issues, str):
        try:
            issues = json.loads(issues)
        except Exception:
            issues = []

    one_line_verdict = roast.get("one_line_verdict", "Resume needs major overhaul.")
    overall_score = roast.get("overall_score", 50)

    # 1. Build script
    script = roast.get("voice_script")
    if not script:
        script = voice_service.build_voice_roast_script(
            one_line_verdict=one_line_verdict,
            issues=issues,
            overall_score=overall_score,
        )

    # 2. Generate audio
    audio_path = voice_service.generate_voice_roast_audio(roast_id, script)
    if roast_id not in ("demo", "demo-roast", "sample-roast-1"):
        database.update_roast_voice(roast_id, script, audio_path)

    # Calculate approximate duration based on word count (~130 words per minute)
    word_count = len(script.split())
    approx_duration = max(18, min(45, int((word_count / 130) * 60)))

    return JSONResponse(
        content={
            "roast_id": roast_id,
            "script": script,
            "duration_seconds": approx_duration,
            "audio_url": f"/api/roast/{roast_id}/voice/audio",
            "disclaimer": "AI-generated voice, for fun — not a real recruiter.",
        }
    )


@router.get("/{roast_id}/voice/audio")
async def get_voice_audio(roast_id: str) -> FileResponse:
    """
    Stream or download the cached voice roast MP3 audio file.
    """
    audio_path = voice_service.get_cached_voice_audio_path(roast_id)
    if not audio_path or not os.path.exists(audio_path):
        # Generate on the fly if roast exists
        if roast_id in ("demo", "demo-roast", "sample-roast-1"):
            roast = DEMO_VOICE_ROAST
        else:
            roast = database.get_roast(roast_id)

        if not roast:
            raise HTTPException(status_code=404, detail="Voice note audio not found.")

        issues = roast.get("issues", [])
        if isinstance(issues, str):
            try:
                issues = json.loads(issues)
            except Exception:
                issues = []

        script = voice_service.build_voice_roast_script(
            one_line_verdict=roast.get("one_line_verdict", ""),
            issues=issues,
            overall_score=roast.get("overall_score", 50),
        )
        audio_path = voice_service.generate_voice_roast_audio(roast_id, script)

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=f"resume-roast-voice-{roast_id[:8]}.mp3",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=86400",
        },
    )
