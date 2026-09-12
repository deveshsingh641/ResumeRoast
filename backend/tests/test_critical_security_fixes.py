import os
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.pro_auth import create_pro_token, verify_pro_token

client = TestClient(app)

def test_critical_a_payment_bypass_closed_when_configured():
    """
    Test A: Verify that POST /api/verify-payment rejects 'order_sim_' or 'pay_sim_' 
    with 400 when Razorpay is configured.
    """
    mock_rzp = {
        "key_id": "rzp_test_12345",
        "key_secret": "test_secret_abcde",
        "webhook_secret": "wh_sec",
        "is_configured": True,
        "mode": "test",
    }
    with patch("app.routers.payment.get_razorpay_config", return_value=mock_rzp):
        # Attacker tries to bypass with order_sim_ prefix
        payload = {
            "razorpay_order_id": "order_sim_bypass123",
            "razorpay_payment_id": "pay_fake_999",
            "razorpay_signature": "fake_signature",
            "email": "attacker@example.com"
        }
        res = client.post("/api/verify-payment", json=payload)
        assert res.status_code == 400
        assert "Simulation payment credentials are not permitted" in res.json().get("detail", "")

        # Repeat for /api/reconcile
        res_rec = client.post("/api/reconcile", json={
            "order_id": "order_sim_bypass123",
            "payment_id": "pay_sim_999",
            "email": "attacker@example.com"
        })
        assert res_rec.status_code == 400
        assert "Simulation payment credentials cannot be reconciled" in res_rec.json().get("detail", "")


def test_critical_b_simulation_still_works_when_unconfigured():
    """
    Test B: Verify that in local dev (Razorpay unconfigured), simulation mode works.
    """
    mock_rzp = {
        "key_id": "",
        "key_secret": "",
        "webhook_secret": "",
        "is_configured": False,
        "mode": "simulation",
    }
    with patch("app.routers.payment.get_razorpay_config", return_value=mock_rzp):
        payload = {
            "razorpay_order_id": "order_sim_dev123",
            "razorpay_payment_id": "pay_sim_dev999",
            "razorpay_signature": "sim_signature",
            "email": "devuser@example.com"
        }
        res = client.post("/api/verify-payment", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data.get("status") == "success"
        assert "pro_token" in data
        # Token must be valid
        claims_email = verify_pro_token(data["pro_token"])
        assert claims_email == "devuser@example.com"


def test_critical_c_usage_limit_bypass_closed():
    """
    Test C: Verify that rotating X-Device-Fingerprint does not bypass rate limit
    from the same IP once the free tier limit is reached.
    """
    client.cookies.clear()
    mock_roast = {
        "overall_score": 60,
        "band": "average",
        "one_line_verdict": "Not bad",
        "summary": "Decent summary",
        "detailed_critique": "Solid experience",
        "issues": [],
        "strengths": ["Clear skills"],
        "fixes": [],
        "improved_bullets": [],
        "ats_score": 75,
        "recruiter_reaction": "Okay",
        "interview_probability": "50%",
    }
    with patch("app.routers.roast.FREE_TIER_LIMIT", 1), \
         patch("app.routers.roast.extractor.extract_text", return_value=("Sample resume text with Python and Docker", False)), \
         patch("app.routers.roast.analyze_resume", return_value=mock_roast):
        # Setup mock file upload
        files = {"file": ("resume1.pdf", b"%PDF-1.4 sample pdf content 1", "application/pdf")}
        
        # 1st roast succeeds
        r1 = client.post(
            "/api/roast",
            files=files,
            headers={"X-Device-Fingerprint": "fp_rotate_1", "User-Agent": "TestClient/1.0", "X-Forwarded-For": "203.0.113.195"}
        )
        assert r1.status_code == 200

        # 2nd roast with rotated X-Device-Fingerprint from SAME IP must be rejected with 429
        files2 = {"file": ("resume2.pdf", b"%PDF-1.4 sample pdf content 2", "application/pdf")}
        r2 = client.post(
            "/api/roast",
            files=files2,
            headers={"X-Device-Fingerprint": "fp_rotate_2", "User-Agent": "TestClient/1.0", "X-Forwarded-For": "203.0.113.195"}
        )
        assert r2.status_code == 429
        assert r2.json().get("detail", {}).get("error") == "daily_limit_reached"


def test_critical_d_entitlement_spoofing_closed():
    """
    Test D: Verify that claiming a Pro user's email in X-User-Email header without
    a cryptographic Pro token does not grant Pro treatment.
    """
    client.cookies.clear()
    # Create or mark user as pro in database
    from app.db import database
    database.update_subscription("real_pro_user@example.com", "pro", "sub_real_123")

    # Attacker tries to impersonate via X-User-Email
    res = client.get(
        "/api/usage",
        headers={"X-User-Email": "real_pro_user@example.com"}
    )
    assert res.status_code == 200
    data = res.json()
    # Should NOT be granted pro without token
    assert data.get("is_pro") is False
    assert data.get("remaining") < 999999

    # Now provide legitimate pro_token
    token = create_pro_token("real_pro_user@example.com")
    res_auth = client.get(
        "/api/usage",
        headers={"X-Pro-Token": token}
    )
    assert res_auth.status_code == 200
    data_auth = res_auth.json()
    assert data_auth.get("is_pro") is True
    assert data_auth.get("remaining") == 999999


def test_critical_e_admin_fail_closed():
    """
    Test E: Verify that when ADMIN_SECRET_KEY is unset, admin access is rejected (fails closed).
    """
    from app.services.admin_auth import verify_admin_access
    from fastapi import Request

    with patch.dict(os.environ, {"ADMIN_SECRET_KEY": ""}, clear=False):
        # Create a mock request with header
        scope = {
            "type": "http",
            "headers": [(b"x-admin-key", b"some_guess")]
        }
        req = Request(scope)
        assert verify_admin_access(req) is False

        # Empty header also fails
        scope_empty = {
            "type": "http",
            "headers": []
        }
        req_empty = Request(scope_empty)
        assert verify_admin_access(req_empty) is False


def test_critical_f_subscription_auth_and_cancellation():
    """
    Test F: Verify POST /subscription/cancel requires authenticated Pro token or Admin key.
    """
    client.cookies.clear()
    from app.db import database
    database.update_subscription("victim@example.com", "pro", "sub_victim")

    # Unauthenticated cancel attempt
    res = client.post("/api/subscription/cancel", json={"email": "victim@example.com"})
    assert res.status_code == 401
    assert "Unauthorized" in res.json().get("detail", "")
    assert database.get_user_subscription("victim@example.com") == "pro"

    # Cancel with victim's valid token succeeds
    token = create_pro_token("victim@example.com")
    res_cancel = client.post(
        "/api/subscription/cancel",
        json={"email": "victim@example.com"},
        headers={"X-Pro-Token": token}
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json().get("status") == "cancelled"
    assert database.get_user_subscription("victim@example.com") == "free"
