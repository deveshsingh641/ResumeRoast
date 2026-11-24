"""
Tests for Feature: Weekly Automated & Manual Wall of Fame / Shame Rotation
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import database
from app.services import wall_service

client = TestClient(app)


def test_weekly_wall_rotation_logic():
    # 1. Clean slate in memory
    database._wall_entries_memory.clear()
    database._last_wall_rotation_date = None

    # 2. Add sample candidate roasts in memory
    roast_fame_id = database.save_roast(
        overall_score=88,
        band="strong",
        one_line_verdict="Solid candidate at Google with 45% latency reduction! contact: test@gmail.com 9876543210",
        issues=[
            {"roast": "Google scale mentioned without proof at https://google.com/test"},
            {"roast": "Great leadership at Microsoft but no metrics"},
        ],
        strengths=["Quantified impact"],
    )

    roast_shame_id = database.save_roast(
        overall_score=25,
        band="weak",
        one_line_verdict="Buzzword museum at Amazon with zero code! reach out at dev@amazon.com",
        issues=[
            {"roast": "Synergized and orchestrated at TCS but no verifiable output"},
            {"roast": "Hobbies include surfing internet from bits pilani"},
        ],
        strengths=[],
    )

    # 3. Trigger rotation
    res = wall_service.rotate_weekly_wall(force=True, limit_per_category=2)
    assert res["rotated"] is True
    assert res["fame_count"] >= 1
    assert res["shame_count"] >= 1

    # 4. Check wall feed has the sanitized entries
    feed_fame = database.get_wall_entries("fame")
    assert feed_fame["total"] >= 1
    fame_item = next((i for i in feed_fame["items"] if i.get("roast_id") == roast_fame_id), None)
    assert fame_item is not None
    assert fame_item["score"] == 88
    # Assert PII sanitization: email, phone, company, and URL scrubbed
    assert "test@gmail.com" not in fame_item["one_line_verdict"]
    assert "[Email]" in fame_item["one_line_verdict"]
    assert "9876543210" not in fame_item["one_line_verdict"]
    assert "[Phone]" in fame_item["one_line_verdict"]
    assert "[Org]" in fame_item["one_line_verdict"]

    feed_shame = database.get_wall_entries("shame")
    assert feed_shame["total"] >= 1
    shame_item = next((i for i in feed_shame["items"] if i.get("roast_id") == roast_shame_id), None)
    assert shame_item is not None
    assert shame_item["score"] == 25
    assert "dev@amazon.com" not in shame_item["one_line_verdict"]
    assert "[Email]" in shame_item["one_line_verdict"]

    # 5. Idempotent check: calling again with force=False should not rotate
    res_second = wall_service.rotate_weekly_wall(force=False)
    assert res_second["rotated"] is False
    assert "Already rotated" in res_second["reason"]


def test_admin_wall_rotate_endpoint():
    # Unauthorized without founder key
    unauth = client.post("/api/admin/wall/rotate")
    assert unauth.status_code == 401

    # Authorized with founder key
    auth_resp = client.post(
        "/api/admin/wall/rotate?force=true",
        headers={"X-Admin-Key": "devesh666"},
    )
    assert auth_resp.status_code == 200
    data = auth_resp.json()
    assert data["ok"] is True
    assert "week" in data
