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
        # Section 0B: pro_token must NEVER be returned in JSON response body
        assert "pro_token" not in data
        # Token must be in HttpOnly cookie
        cookie_token = res.cookies.get("resumeroast_pro_token")
        assert cookie_token is not None
        claims_email = verify_pro_token(cookie_token)
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
         patch("app.routers.roast.IP_SHARED_LIMIT", 1), \
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
    from app.db import database
    database.create_or_get_user("real_pro_user@example.com")
    database.update_subscription("real_pro_user@example.com", "pro", "sub_real_123")

    mock_roast = {
        "overall_score": 70,
        "band": "average",
        "one_line_verdict": "Okay",
        "issues": [{"quoted_text": f"Issue {i}", "category": "formatting", "roast": "r", "fix": "f"} for i in range(5)],
        "strengths": ["Clear skills"],
    }
    with patch("app.routers.roast.extractor.extract_text", return_value=("Real pro text", False)), \
         patch("app.routers.roast.analyze_resume", return_value=mock_roast):
        # Attacker spoofs real_pro_user@example.com via X-User-Email
        files = {"file": ("resume_spoof.pdf", b"%PDF-1.4 spoof", "application/pdf")}
        r_spoof = client.post(
            "/api/roast",
            files=files,
            headers={"X-User-Email": "real_pro_user@example.com", "X-Device-Fingerprint": "spoof_fp_1"}
        )
        assert r_spoof.status_code == 200
        # Must be treated as free tier (truncated issues), NOT Pro
        data = r_spoof.json()
        assert data.get("is_truncated") is True
        assert len(data.get("issues", [])) == 3

    # Now provide legitimate pro_token
    token = create_pro_token("real_pro_user@example.com")
    with patch("app.routers.roast.extractor.extract_text", return_value=("Real pro text 2", False)), \
         patch("app.routers.roast.analyze_resume", return_value=mock_roast):
        files_pro = {"file": ("resume_legit.pdf", b"%PDF-1.4 legit", "application/pdf")}
        r_pro = client.post(
            "/api/roast",
            files=files_pro,
            cookies={"resumeroast_pro_token": token}
        )
        assert r_pro.status_code == 200
        data_pro = r_pro.json()
        assert data_pro.get("is_truncated") is False
        assert len(data_pro.get("issues", [])) == 5


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


# ===========================================================================
# Round 2 Tests (Section 0A - 0F Verifications)
# ===========================================================================

def test_section_0a_token_secret_key_enforcement():
    """
    Section 0A (Test A):
    Unset TOKEN_SECRET_KEY, ADMIN_SECRET_KEY, and RAZORPAY_KEY_SECRET.
    Confirm create_pro_token raises RuntimeError, verify_pro_token fails closed (None),
    and production startup validation fails fast with RuntimeError.
    """
    from app.services.pro_auth import _get_signing_key
    from app.main import validate_startup_environment

    with patch.dict(
        os.environ,
        {
            "TOKEN_SECRET_KEY": "",
            "ADMIN_SECRET_KEY": "",
            "RAZORPAY_KEY_SECRET": "",
            "ENVIRONMENT": "production",
            "STRICT_STARTUP_SECRETS": "true",
        },
        clear=False,
    ):
        # 1. _get_signing_key must raise RuntimeError without fallback to hardcoded string
        with pytest.raises(RuntimeError, match="TOKEN_SECRET_KEY"):
            _get_signing_key()

        # 2. create_pro_token must fail
        with pytest.raises(RuntimeError, match="TOKEN_SECRET_KEY"):
            create_pro_token("test@example.com")

        # 3. verify_pro_token must fail closed (return None)
        assert verify_pro_token("invalid.token.structure") is None
        assert verify_pro_token("abc.123") is None

        # 4. Production startup validation must hard-fail
        with pytest.raises(RuntimeError):
            validate_startup_environment()


def test_section_0b_pro_token_cookie_only_not_in_json():
    """
    Section 0B (Test B):
    Verify that upon successful payment verification or reconcile, pro_token is
    NEVER returned in the JSON response body, but IS set as an HttpOnly cookie.
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
            "razorpay_order_id": "order_sim_round2",
            "razorpay_payment_id": "pay_sim_round2",
            "razorpay_signature": "sim_signature",
            "email": "cookie_user@example.com",
            "plan": "monthly",
        }
        res = client.post("/api/verify-payment", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body.get("status") == "success"
        # pro_token must NOT be in the JSON payload
        assert "pro_token" not in body

        # Cookie must be set with correct attributes
        cookie_token = res.cookies.get("resumeroast_pro_token")
        assert cookie_token is not None
        assert verify_pro_token(cookie_token) == "cookie_user@example.com"

        # Check Set-Cookie header contains HttpOnly and SameSite=lax
        set_cookie_header = res.headers.get("set-cookie", "").lower()
        assert "httponly" in set_cookie_header
        assert "samesite=lax" in set_cookie_header


def test_section_0c_fair_shared_cgnat_usage_threshold():
    """
    Section 0C (Test C):
    Simulate multiple distinct device fingerprints from the same IP.
    Under IP_SHARED_LIMIT = 5:
    - User 1 (Device A) succeeds.
    - User 1 (Device A) again is blocked (fingerprint limit 1/day).
    - User 2 (Device B) from same IP succeeds (fair CGNAT sharing).
    - User 3 (Device C) from same IP succeeds.
    - Once 5 different devices from same IP roast, 6th device is blocked by shared IP limit.
    """
    from app.db import database
    client.cookies.clear()
    mock_roast = {
        "overall_score": 65,
        "band": "average",
        "one_line_verdict": "Good",
        "issues": [],
        "strengths": ["Skills"],
    }
    test_ip = "198.51.100.77"

    with patch("app.routers.roast.FREE_TIER_LIMIT", 1), \
         patch("app.routers.roast.IP_SHARED_LIMIT", 3), \
         patch("app.routers.roast.extractor.extract_text", return_value=("Resume text", False)), \
         patch("app.routers.roast.analyze_resume", return_value=mock_roast):

        # Device 1 from shared IP
        f1 = {"file": ("r1.pdf", b"%PDF-1.4 test 1", "application/pdf")}
        r1 = client.post(
            "/api/roast",
            files=f1,
            headers={"X-Device-Fingerprint": "cgnat_dev_1", "User-Agent": "Mobile-A", "X-Forwarded-For": test_ip}
        )
        assert r1.status_code == 200

        # Device 1 again from shared IP -> blocked because Device 1 reached FREE_TIER_LIMIT
        f1_again = {"file": ("r1b.pdf", b"%PDF-1.4 test 1b", "application/pdf")}
        r1_again = client.post(
            "/api/roast",
            files=f1_again,
            headers={"X-Device-Fingerprint": "cgnat_dev_1", "User-Agent": "Mobile-A", "X-Forwarded-For": test_ip}
        )
        assert r1_again.status_code == 429
        assert "used your 1 free roast" in r1_again.json()["detail"]["message"]

        # Device 2 (different student on same hostel/mobile CGNAT IP) -> SUCCEEDS!
        f2 = {"file": ("r2.pdf", b"%PDF-1.4 test 2", "application/pdf")}
        r2 = client.post(
            "/api/roast",
            files=f2,
            headers={"X-Device-Fingerprint": "cgnat_dev_2", "User-Agent": "Mobile-B", "X-Forwarded-For": test_ip}
        )
        assert r2.status_code == 200

        # Device 3 from same IP -> SUCCEEDS (hits IP limit of 3)
        f3 = {"file": ("r3.pdf", b"%PDF-1.4 test 3", "application/pdf")}
        r3 = client.post(
            "/api/roast",
            files=f3,
            headers={"X-Device-Fingerprint": "cgnat_dev_3", "User-Agent": "Mobile-C", "X-Forwarded-For": test_ip}
        )
        assert r3.status_code == 200

        # Device 4 from same IP -> BLOCKED because IP_SHARED_LIMIT (3) is reached
        f4 = {"file": ("r4.pdf", b"%PDF-1.4 test 4", "application/pdf")}
        r4 = client.post(
            "/api/roast",
            files=f4,
            headers={"X-Device-Fingerprint": "cgnat_dev_4", "User-Agent": "Mobile-D", "X-Forwarded-For": test_ip}
        )
        assert r4.status_code == 429
        assert "limit reached for this network" in r4.json()["detail"]["message"]


def test_section_0f_subscription_status_rate_limited_and_no_enumeration():
    """
    Section 0F (Test F):
    1. Unauthenticated query to /api/subscription/status returns generic {is_pro: false, authenticated: false}
       without disclosing whether an arbitrary email is a paying Pro subscriber.
    2. Authenticated query with matching Pro token or Admin key returns true and subscription details.
    3. Endpoint enforces rate limiting.
    """
    from app.db import database
    client.cookies.clear()
    target_email = "vip_subscriber@example.com"
    database.create_or_get_user(target_email)
    database.update_subscription(target_email, "pro", "sub_vip_123")

    # 1. Unauthenticated attacker probes target_email -> Gets generic false, authenticated: false
    res_unauth = client.get(f"/api/subscription/status?email={target_email}")
    assert res_unauth.status_code == 200
    data_unauth = res_unauth.json()
    assert data_unauth["is_pro"] is False
    assert data_unauth["authenticated"] is False
    assert "subscription_status" not in data_unauth

    # 2. Authenticated user queries own email -> Receives is_pro: True and subscription status
    valid_token = create_pro_token(target_email)
    res_auth = client.get(
        f"/api/subscription/status?email={target_email}",
        cookies={"resumeroast_pro_token": valid_token}
    )
    assert res_auth.status_code == 200
    data_auth = res_auth.json()
    assert data_auth["is_pro"] is True
    assert data_auth["authenticated"] is True
    assert data_auth["subscription_status"] == "pro"
    assert data_auth["email"] == target_email
