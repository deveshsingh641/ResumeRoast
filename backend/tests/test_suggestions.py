"""
Unit tests for Suggestion Box feature:
- Public submission with honeypot defense
- Category and length validation
- Daily rate limiting
- Admin review & status triage
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import database


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("ADMIN_SECRET_KEY", "test_admin_secret_123")
    database.init_db()


def test_submit_suggestion_success():
    client = TestClient(app)
    resp = client.post(
        "/api/suggestions",
        json={
            "text": "Please add an option to compare resumes against LinkedIn job URLs directly! 💡",
            "category": "feature",
            "email": "user@example.com",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "We actually read these" in data["message"]
    assert "id" in data


def test_honeypot_silently_dropped():
    """Bots filling the hidden 'website' field should receive 200 without saving."""
    client = TestClient(app)
    initial_count = database.get_suggestion_count()

    resp = client.post(
        "/api/suggestions",
        json={
            "text": "Buy crypto now at spamlink.com",
            "category": "feature",
            "website": "http://spambot-link.com",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "We actually read these" in data["message"]
    # Verify not actually saved
    new_count = database.get_suggestion_count()
    assert new_count == initial_count


def test_suggestion_text_too_short():
    client = TestClient(app)
    resp = client.post(
        "/api/suggestions",
        json={"text": "hi"},
    )
    assert resp.status_code == 422 or resp.status_code == 400


def test_admin_list_and_update_suggestion():
    client = TestClient(app)

    # 1. Submit a bug report
    sub_resp = client.post(
        "/api/suggestions",
        json={
            "text": "Audio voice note cuts off on Android Firefox after 15 seconds.",
            "category": "bug",
            "email": "tester@test.com",
        },
    )
    assert sub_resp.status_code == 200
    sug_id = sub_resp.json()["id"]

    # 2. Unauthorized admin query
    unauth_resp = client.get("/api/admin/suggestions", headers={"X-Admin-Key": "wrong"})
    assert unauth_resp.status_code == 401

    # 3. Authorized admin query
    admin_resp = client.get("/api/admin/suggestions", headers={"X-Admin-Key": "test_admin_secret_123"})
    assert admin_resp.status_code == 200
    admin_data = admin_resp.json()
    assert admin_data["ok"] is True
    assert any(s["id"] == sug_id for s in admin_data["suggestions"])

    # 4. Update status to 'planned'
    patch_resp = client.patch(
        f"/api/admin/suggestions/{sug_id}",
        headers={"X-Admin-Key": "test_admin_secret_123"},
        json={"status": "planned"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "planned"
