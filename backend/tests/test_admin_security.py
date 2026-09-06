"""
Security test suite for Founder Dashboard and Admin Endpoints.
Verifies:
1. Unauthorized requests are strictly blocked (401).
2. Brute-force rate limiting locks out IP after 5 failed attempts (429).
3. Secure no-cache headers are applied to all confidential admin responses.
4. Candidate resumes endpoint (/api/admin/roasts) is strictly protected.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import admin_auth


@pytest.fixture(autouse=True)
def setup_security_env(monkeypatch):
    monkeypatch.setenv("ADMIN_SECRET_KEY", "ultra_secure_founder_key_2026")
    admin_auth._failed_attempts.clear()


def test_candidate_resumes_strictly_protected():
    client = TestClient(app)
    # Unauthenticated request MUST be rejected with 401
    resp = client.get("/api/admin/roasts")
    assert resp.status_code == 401
    assert "Unauthorized" in resp.json().get("detail", "")


def test_candidate_resumes_authorized_access():
    client = TestClient(app)
    resp = client.get(
        "/api/admin/roasts",
        headers={"X-Admin-Key": "ultra_secure_founder_key_2026"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert "no-store" in resp.headers.get("Cache-Control", "")


def test_admin_metrics_no_cache_headers():
    client = TestClient(app)
    resp = client.get(
        "/api/admin/metrics",
        headers={"X-Admin-Key": "ultra_secure_founder_key_2026"},
    )
    assert resp.status_code == 200
    assert "no-store" in resp.headers.get("Cache-Control", "")
    assert "no-cache" in resp.headers.get("Pragma", "")
    assert resp.headers.get("X-Frame-Options") == "DENY"


def test_brute_force_lockout_after_five_failed_attempts():
    client = TestClient(app)

    # 4 failed attempts should return 401
    for i in range(4):
        resp = client.get("/api/admin/metrics", headers={"X-Admin-Key": f"wrong_key_{i}"})
        assert resp.status_code == 401

    # 5th failed attempt: still 401, but records 5th failure
    resp5 = client.get("/api/admin/metrics", headers={"X-Admin-Key": "wrong_key_5"})
    assert resp5.status_code == 401

    # 6th attempt: MUST trigger 429 Security Lockout!
    resp_lockout = client.get("/api/admin/metrics", headers={"X-Admin-Key": "wrong_key_6"})
    assert resp_lockout.status_code == 429
    assert "Security lockout" in resp_lockout.json().get("detail", "")

    # Even if attacker now guesses the correct key, they are LOCKED OUT!
    locked_correct = client.get(
        "/api/admin/metrics",
        headers={"X-Admin-Key": "ultra_secure_founder_key_2026"},
    )
    assert locked_correct.status_code == 429
    assert "Security lockout" in locked_correct.json().get("detail", "")


def test_candidate_resumes_deduplication():
    client = TestClient(app)
    # 1. Fetch with unique=true (default)
    resp_unique = client.get(
        "/api/admin/roasts?unique=true&limit=100",
        headers={"X-Admin-Key": "ultra_secure_founder_key_2026"},
    )
    assert resp_unique.status_code == 200
    data_u = resp_unique.json()
    assert data_u["ok"] is True
    assert "total_unique" in data_u
    assert "total_all" in data_u
    assert data_u["unique_only"] is True
    # Ensure total_unique <= total_all
    assert data_u["total_unique"] <= data_u["total_all"]

    # 2. Fetch with unique=false
    resp_all = client.get(
        "/api/admin/roasts?unique=false&limit=100",
        headers={"X-Admin-Key": "ultra_secure_founder_key_2026"},
    )
    assert resp_all.status_code == 200
    data_a = resp_all.json()
    assert data_a["unique_only"] is False
    assert data_a["total"] == data_u["total_all"]

