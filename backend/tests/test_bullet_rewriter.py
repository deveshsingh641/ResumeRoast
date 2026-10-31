"""
Unit tests for AI Resume Bullet Rewriter
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.bullet_rewriter import _fallback_bullet_rewrite, rewrite_bullet


@pytest.mark.anyio
async def test_fallback_bullet_rewrite_structure():
    original = "Assisted with database management and writing queries"
    res = _fallback_bullet_rewrite(original, target_role="Backend Developer")

    assert res.original == original
    assert res.target_role == "Backend Developer"
    assert res.source == "fallback"
    assert len(res.options) == 3

    styles = [opt.style for opt in res.options]
    assert "Impact & Metrics (STAR)" in styles
    assert "Action & Leadership" in styles
    assert "ATS-Optimized Concise" in styles

    for opt in res.options:
        assert len(opt.rewritten_text) > 10
        assert len(opt.explanation) > 10
        assert opt.badge


@pytest.mark.anyio
async def test_rewrite_bullet_empty_or_short():
    res = await rewrite_bullet("bad")
    assert res.source == "fallback"
    assert len(res.options) == 3


def test_rewrite_bullet_endpoint():
    client = TestClient(app)
    response = client.post(
        "/api/rewrite-bullet",
        json={
            "bullet": "Worked on frontend bugs and helped with releases",
            "target_role": "Frontend Engineer",
            "language": "en",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "data" in data
    assert len(data["data"]["options"]) == 3
    assert data["data"]["target_role"] == "Frontend Engineer"


def test_rewrite_bullet_validation():
    client = TestClient(app)
    # Empty bullet
    res_empty = client.post("/api/rewrite-bullet", json={"bullet": "   "})
    assert res_empty.status_code == 422

    # Overly long bullet
    res_long = client.post("/api/rewrite-bullet", json={"bullet": "x" * 1050})
    assert res_long.status_code == 422
