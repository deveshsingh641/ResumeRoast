"""
Unit tests for AI Interview Hot-Seat & Trap Question Griller Service
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.interview_griller import (
    _generate_smart_fallback_questions,
    generate_interview_prep,
)


@pytest.mark.anyio
async def test_fallback_interview_prep_structure():
    mock_roast = {
        "overall_score": 42,
        "band": "mid",
        "one_line_verdict": "Vague claims and buzzword soup",
        "issues": [
            {
                "quoted_text": "Assisted with building REST APIs",
                "category": "no-metrics",
                "roast": "Assisted matlab kya kiya bhai?",
                "fix": "Built 5 REST APIs with 99.9% uptime",
            },
            {
                "quoted_text": "Worked with cross-functional teams",
                "category": "buzzword",
                "roast": "Very generic claim",
                "fix": "Partnered with 3 product managers to ship v2",
            },
        ],
    }

    res = _generate_smart_fallback_questions(mock_roast, roast_id="test-123", language="en")
    assert res.roast_id == "test-123"
    assert res.source == "smart_engine"
    assert len(res.questions) == 3

    q1 = res.questions[0]
    assert "Assisted with building REST APIs" in q1.flaw_reference or "vague" in q1.question.lower()
    assert q1.category
    assert q1.difficulty in ("Brutal", "Tough", "Crucial")
    assert len(q1.question) > 20
    assert len(q1.interviewer_trap) > 10
    assert len(q1.rookie_blunder) > 10
    assert q1.star_framework.situation_task
    assert q1.star_framework.action
    assert q1.star_framework.result
    assert len(q1.script_to_say) > 20


@pytest.mark.anyio
async def test_generate_interview_prep_async():
    mock_roast = {
        "overall_score": 30,
        "issues": [
            {"quoted_text": "Responsible for testing code", "category": "no-metrics"}
        ],
    }
    res = await generate_interview_prep(mock_roast, roast_id="async-test")
    assert len(res.questions) >= 2


def test_interview_prep_endpoint_demo():
    client = TestClient(app)
    response = client.get("/api/roast/demo/interview-prep")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data.get("ok") is True
    data = json_data.get("data", {})
    assert "questions" in data
    assert len(data["questions"]) >= 3
    assert data["questions"][0]["question"]


def test_interview_prep_endpoint_404():
    client = TestClient(app)
    response = client.get("/api/roast/non-existent-uuid-9999/interview-prep")
    assert response.status_code == 404
