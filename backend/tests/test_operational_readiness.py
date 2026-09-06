"""
Unit tests for Operational Readiness infrastructure:
- Thread-safe DB Connection Pooling
- Founder Metrics Dashboard (/api/admin/metrics)
- Customer Support Pro Manual Override (/api/admin/user/override-pro)
"""
import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import database


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("ADMIN_SECRET_KEY", "test_admin_secret_123")
    database.init_db()


def test_admin_metrics_endpoint_unauthorized():
    client = TestClient(app)
    resp = client.get("/api/admin/metrics", headers={"X-Admin-Key": "wrong_key"})
    assert resp.status_code == 401
    assert "Unauthorized" in resp.json().get("detail", "")


def test_admin_metrics_endpoint_authorized():
    client = TestClient(app)
    resp = client.get("/api/admin/metrics", headers={"X-Admin-Key": "test_admin_secret_123"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "summary" in data
    assert "costs" in data
    assert "traffic_7d" in data
    assert "infrastructure" in data
    assert "total_roasts_all_time" in data["summary"]
    assert "waitlist_signups" in data["summary"]
    assert data["costs"]["cost_per_roast_gemini_flash_usd"] == 0.0003


def test_support_override_grant_and_revoke_pro():
    client = TestClient(app)
    test_user_email = "support_test_user@example.com"

    # 1. Initially free
    assert database.get_user_subscription(test_user_email) == "free"

    # 2. Grant Pro via Support Endpoint
    grant_resp = client.post(
        "/api/admin/user/override-pro",
        headers={"X-Admin-Key": "test_admin_secret_123"},
        json={
            "email": test_user_email,
            "action": "grant_pro",
            "reason": "Payment verified via manual UPI reference",
        },
    )
    assert grant_resp.status_code == 200
    grant_data = grant_resp.json()
    assert grant_data["ok"] is True
    assert grant_data["subscription_status"] == "pro"
    assert database.get_user_subscription(test_user_email) == "pro"

    # 3. Revoke Pro
    revoke_resp = client.post(
        "/api/admin/user/override-pro",
        headers={"X-Admin-Key": "test_admin_secret_123"},
        json={
            "email": test_user_email,
            "action": "revoke_pro",
            "reason": "Refund requested and processed",
        },
    )
    assert revoke_resp.status_code == 200
    revoke_data = revoke_resp.json()
    assert revoke_data["subscription_status"] == "free"
    assert database.get_user_subscription(test_user_email) == "free"


def test_support_override_invalid_email():
    client = TestClient(app)
    resp = client.post(
        "/api/admin/user/override-pro",
        headers={"X-Admin-Key": "test_admin_secret_123"},
        json={"email": "not-an-email", "action": "grant_pro"},
    )
    assert resp.status_code == 400


def test_db_connection_pooling_context_manager_safety():
    """Verify _get_conn raises clear error when DATABASE_URL is not configured."""
    with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
        with database._get_conn():
            pass
