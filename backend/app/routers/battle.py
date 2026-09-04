"""
Roast Battle Router — 1-on-1 resume comparison endpoint with comparative AI refereeing.
"""
from __future__ import annotations

import json
import os
from typing import Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.db import database
from app.i18n.mapping import DEFAULT_LANGUAGE, language_from_request
from app.routers.roast import _device_fingerprint, MAX_FILE_SIZE
from app.services import ai_analyzer, battle_service, extractor

router = APIRouter(prefix="/api", tags=["battle"])


@router.post("/battle")
async def create_battle(
    request: Request,
    fighter1: UploadFile = File(...),
    fighter2: UploadFile = File(...),
) -> JSONResponse:
    """
    Runs both resumes through the analysis pipeline and produces comparative battle verdict.
    """
    # 1. Read files
    try:
        f1_bytes = await fighter1.read()
        f2_bytes = await fighter2.read()
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="File upload was interrupted. Please try again.",
        )

    if len(f1_bytes) == 0 or len(f2_bytes) == 0:
        raise HTTPException(
            status_code=422,
            detail="Both fighter resumes must be non-empty valid documents.",
        )

    if len(f1_bytes) > MAX_FILE_SIZE or len(f2_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="One or both files exceed the 5MB limit.",
        )

    # 2. Extract text for Fighter 1
    try:
        f1_text, _ = extractor.extract_text(
            fighter1.filename or "fighter1.pdf", fighter1.content_type or "", f1_bytes
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Fighter 1 file error: {str(e)}")

    # 3. Extract text for Fighter 2
    try:
        f2_text, _ = extractor.extract_text(
            fighter2.filename or "fighter2.pdf", fighter2.content_type or "", f2_bytes
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Fighter 2 file error: {str(e)}")

    # 4. Analyze both resumes
    lang = language_from_request(request)
    try:
        f1_analysis = ai_analyzer.analyze_resume(f1_text, language=lang)
        f2_analysis = ai_analyzer.analyze_resume(f2_text, language=lang)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to analyze resumes during battle.")

    # 5. Comparative battle referee AI
    comparison = battle_service.analyze_battle(f1_analysis, f2_analysis, language=lang)

    fingerprint = _device_fingerprint(request)

    # 6. Save battle to DB
    battle_id = database.save_battle(
        fighter_1_score=f1_analysis["overall_score"],
        fighter_1_band=f1_analysis["band"],
        fighter_1_verdict=f1_analysis["one_line_verdict"],
        fighter_1_issues=f1_analysis["issues"],
        fighter_1_strengths=f1_analysis["strengths"],
        fighter_2_score=f2_analysis["overall_score"],
        fighter_2_band=f2_analysis["band"],
        fighter_2_verdict=f2_analysis["one_line_verdict"],
        fighter_2_issues=f2_analysis["issues"],
        fighter_2_strengths=f2_analysis["strengths"],
        winner=comparison["winner"],
        margin=comparison["margin"],
        verdict=comparison["verdict"],
        fighter_1_best_line=comparison.get("fighter_1_best_line", ""),
        fighter_2_best_line=comparison.get("fighter_2_best_line", ""),
        device_fingerprint=fingerprint,
    )

    return JSONResponse(
        content={
            "id": battle_id,
            "fighter_1": {
                "name": fighter1.filename or "Fighter 1",
                "overall_score": f1_analysis["overall_score"],
                "band": f1_analysis["band"],
                "one_line_verdict": f1_analysis["one_line_verdict"],
                "issues": f1_analysis["issues"][:3],
                "total_issues": len(f1_analysis["issues"]),
                "strengths": f1_analysis["strengths"],
            },
            "fighter_2": {
                "name": fighter2.filename or "Fighter 2",
                "overall_score": f2_analysis["overall_score"],
                "band": f2_analysis["band"],
                "one_line_verdict": f2_analysis["one_line_verdict"],
                "issues": f2_analysis["issues"][:3],
                "total_issues": len(f2_analysis["issues"]),
                "strengths": f2_analysis["strengths"],
            },
            "winner": comparison["winner"],
            "margin": comparison["margin"],
            "verdict": comparison["verdict"],
            "fighter_1_best_line": comparison.get("fighter_1_best_line", ""),
            "fighter_2_best_line": comparison.get("fighter_2_best_line", ""),
        }
    )


@router.get("/battle/{battle_id}")
async def get_battle(battle_id: str) -> JSONResponse:
    """Fetch stored battle by ID."""
    b = database.get_battle(battle_id)
    if not b:
        raise HTTPException(
            status_code=404,
            detail="This battle has expired or does not exist.",
        )

    def _parse_json(val):
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                return []
        return val or []

    f1_issues = _parse_json(b.get("fighter_1_issues"))
    f2_issues = _parse_json(b.get("fighter_2_issues"))

    return JSONResponse(
        content={
            "id": str(b["id"]),
            "fighter_1": {
                "name": "Fighter 1",
                "overall_score": b["fighter_1_score"],
                "band": b["fighter_1_band"],
                "one_line_verdict": b["fighter_1_verdict"],
                "issues": f1_issues[:3],
                "total_issues": len(f1_issues),
                "strengths": _parse_json(b.get("fighter_1_strengths")),
            },
            "fighter_2": {
                "name": "Fighter 2",
                "overall_score": b["fighter_2_score"],
                "band": b["fighter_2_band"],
                "one_line_verdict": b["fighter_2_verdict"],
                "issues": f2_issues[:3],
                "total_issues": len(f2_issues),
                "strengths": _parse_json(b.get("fighter_2_strengths")),
            },
            "winner": b["winner"],
            "margin": b["margin"],
            "verdict": b["verdict"],
            "fighter_1_best_line": b["fighter_1_best_line"],
            "fighter_2_best_line": b["fighter_2_best_line"],
            "created_at": str(b.get("created_at", "")),
        }
    )
