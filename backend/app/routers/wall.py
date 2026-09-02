"""
Wall of Shame / Wall of Fame Router — Opt-in public feed of anonymized roasts.
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.db import database
from app.routers.roast import _device_fingerprint
from app.services import wall_service

router = APIRouter(prefix="/api/wall", tags=["wall"])


class PublishRequest(BaseModel):
    roast_id: str


@router.post("/publish")
async def publish_to_wall(req: PublishRequest, request: Request) -> JSONResponse:
    """
    Publish an existing roast to the public Wall of Shame or Wall of Fame with full anonymization.
    Consent is explicit from the client.
    """
    roast = database.get_roast(req.roast_id)
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

    # Anonymize and categorize
    payload = wall_service.prepare_wall_entry_payload(
        overall_score=roast.get("overall_score", 50),
        band=roast.get("band", "mid"),
        one_line_verdict=roast.get("one_line_verdict", ""),
        issues=issues,
    )

    fingerprint = _device_fingerprint(request)

    # Save anonymized entry to wall table
    wall_id = database.save_wall_entry(
        roast_id=req.roast_id,
        entry_type=payload["type"],
        score=payload["score"],
        band=payload["band"],
        one_line_verdict=payload["one_line_verdict"],
        top_roast_lines=payload["top_roast_lines"],
        device_fingerprint=fingerprint,
    )

    return JSONResponse(
        content={
            "wall_id": wall_id,
            "type": payload["type"],
            "message": f"Successfully published to the Wall of {payload['type'].title()}! All personal identifiers were sanitized.",
        }
    )


@router.get("")
async def get_wall(
    type: str = Query("shame", pattern="^(shame|fame)$"),
    sort: str = Query("recent", pattern="^(recent|score)$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=50),
) -> JSONResponse:
    """
    Public paginated feed of anonymized roasts for Wall of Shame and Wall of Fame.
    """
    result = database.get_wall_entries(
        entry_type=type,
        sort_by=sort,
        page=page,
        limit=limit,
    )
    return JSONResponse(content=result)


@router.post("/{entry_id}/flag")
async def flag_entry(entry_id: str) -> JSONResponse:
    """
    Flag an entry for community moderation. Auto-hides after 3 flags.
    """
    res = database.flag_wall_entry(entry_id)
    if not res.get("found"):
        raise HTTPException(status_code=404, detail="Wall entry not found.")

    return JSONResponse(
        content={
            "status": "flagged",
            "hidden": res["hidden"],
            "message": "Thank you for helping keep the community clean. The entry has been reported.",
        }
    )


@router.post("/admin/{entry_id}/hide")
async def admin_hide_entry(entry_id: str, hidden: bool = True) -> JSONResponse:
    """
    Admin moderation endpoint to hide/unhide flagged entries.
    """
    success = database.hide_wall_entry(entry_id, hidden=hidden)
    if not success:
        raise HTTPException(status_code=404, detail="Wall entry not found.")

    return JSONResponse(
        content={
            "status": "updated",
            "hidden": hidden,
        }
    )
