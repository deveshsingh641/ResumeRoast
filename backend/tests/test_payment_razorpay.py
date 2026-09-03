"""
Comprehensive unit tests for Razorpay Standard Web Checkout, HMAC-SHA256 signature verification,
billing endpoints, and product-wide Pro-tier gating.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.db import database


class TestPaymentRazorpay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig_key_id = os.environ.get("RAZORPAY_KEY_ID", "")
        cls.orig_key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "")
        cls.orig_webhook_secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")

    @classmethod
    def tearDownClass(cls):
        if cls.orig_key_id:
            os.environ["RAZORPAY_KEY_ID"] = cls.orig_key_id
        else:
            os.environ.pop("RAZORPAY_KEY_ID", None)

        if cls.orig_key_secret:
            os.environ["RAZORPAY_KEY_SECRET"] = cls.orig_key_secret
        else:
            os.environ.pop("RAZORPAY_KEY_SECRET", None)

        if cls.orig_webhook_secret:
            os.environ["RAZORPAY_WEBHOOK_SECRET"] = cls.orig_webhook_secret
        else:
            os.environ.pop("RAZORPAY_WEBHOOK_SECRET", None)

    def setUp(self):
        self.client = TestClient(app)
        database.init_db()
        # Restore active credentials for each test
        if self.orig_key_id:
            os.environ["RAZORPAY_KEY_ID"] = self.orig_key_id
        if self.orig_key_secret:
            os.environ["RAZORPAY_KEY_SECRET"] = self.orig_key_secret

    def test_billing_diagnostics(self):
        """Diagnostics endpoint returns healthy environment breakdown."""
        response = self.client.get("/api/billing/diagnostics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["currency"], "INR")
        self.assertIn("plans", data)
        self.assertEqual(data["plans"]["monthly"]["amount_paise"], 29900)
        self.assertEqual(data["plans"]["annual"]["amount_paise"], 249900)

    def test_billing_public_config(self):
        """Public config endpoint exposes safe client values."""
        response = self.client.get("/api/billing/config")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["provider"], "razorpay")
        self.assertEqual(data["currency"], "INR")
        self.assertIn("key_id", data)
        self.assertIn("plans", data)

    def test_create_order_invalid_email(self):
        """Invalid email returns 422 with descriptive validation error."""
        response = self.client.post(
            "/api/create-order",
            json={"email": "not-an-email", "plan": "monthly"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("valid email", response.json()["detail"].lower())

    def test_create_order_amount_under_minimum(self):
        """Amount under 100 paise returns 400 error."""
        response = self.client.post(
            "/api/create-order",
            json={"email": "candidate@example.com", "amount": 50},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("minimum order amount", response.json()["detail"].lower())

    def test_create_order_simulation_mode(self):
        """When keys are absent, creates valid developer simulation order with exact paise."""
        os.environ["RAZORPAY_KEY_ID"] = ""
        os.environ["RAZORPAY_KEY_SECRET"] = ""
        try:
            response = self.client.post(
                "/api/create-order",
                json={"email": "candidate@example.com", "plan": "monthly"},
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["status"], "success")
            self.assertEqual(data["amount"], 29900)
            self.assertEqual(data["currency"], "INR")
            self.assertTrue(data["order_id"].startswith("order_sim_"))
            self.assertTrue(data["simulated"])
        finally:
            if self.orig_key_id:
                os.environ["RAZORPAY_KEY_ID"] = self.orig_key_id
            if self.orig_key_secret:
                os.environ["RAZORPAY_KEY_SECRET"] = self.orig_key_secret

    def test_create_order_real_razorpay_keys(self):
        """When Razorpay test keys are set, creates real Razorpay order with amount & currency."""
        if not self.orig_key_id or not self.orig_key_secret:
            self.skipTest("Razorpay keys not set in environment")

        response = self.client.post(
            "/api/create-order",
            json={"email": "candidate@example.com", "plan": "monthly"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["amount"], 29900)
        self.assertEqual(data["currency"], "INR")
        self.assertTrue(data["order_id"].startswith("order_"))
        self.assertFalse(data["simulated"])

    def test_create_order_annual_plan(self):
        """Annual plan calculates 249900 paise server-side."""
        response = self.client.post(
            "/api/create-order",
            json={"email": "candidate@example.com", "plan": "annual"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["amount"], 249900)

    def test_verify_simulation_payment(self):
        """Verifying simulation payment unlocks Pro in database immediately."""
        email = "testuser_pro@example.com"
        response = self.client.post(
            "/api/verify-payment",
            json={
                "razorpay_order_id": "order_sim_12345678_abcdef",
                "razorpay_payment_id": "pay_sim_987654321",
                "razorpay_signature": "mock_signature",
                "email": email,
                "plan": "monthly",
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_pro"])

        # Check database directly
        status = database.get_user_subscription(email)
        self.assertEqual(status, "pro")

        # Check subscription status route
        status_resp = self.client.get(f"/api/subscription/status?email={email}")
        self.assertEqual(status_resp.status_code, 200)
        self.assertTrue(status_resp.json()["is_pro"])

    def test_verify_payment_missing_fields(self):
        """Missing verification fields returns 400."""
        response = self.client.post(
            "/api/verify-payment",
            json={"razorpay_order_id": "order_123"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("missing required payment verification fields", response.json()["detail"].lower())

    def test_verify_payment_invalid_signature(self):
        """When Razorpay secret is set, mismatched HMAC signature is rejected with 400 and user is NOT paid."""
        os.environ["RAZORPAY_KEY_ID"] = "rzp_test_sample123"
        os.environ["RAZORPAY_KEY_SECRET"] = "secret_sample456"
        email = "unpaid_user@example.com"

        try:
            response = self.client.post(
                "/api/verify-payment",
                json={
                    "razorpay_order_id": "order_real_123",
                    "razorpay_payment_id": "pay_real_456",
                    "razorpay_signature": "invalid_signature_hash",
                    "email": email,
                    "plan": "monthly",
                },
            )
            self.assertEqual(response.status_code, 400)
            self.assertIn("invalid payment signature", response.json()["detail"].lower())

            # User must NOT be pro in DB
            self.assertEqual(database.get_user_subscription(email), "free")

            # Now test with valid cryptographic signature HMAC-SHA256(order_id + "|" + payment_id, KEY_SECRET)
            msg = f"order_real_123|pay_real_456".encode("utf-8")
            valid_sig = hmac.new("secret_sample456".encode("utf-8"), msg, hashlib.sha256).hexdigest()

            valid_response = self.client.post(
                "/api/verify-payment",
                json={
                    "razorpay_order_id": "order_real_123",
                    "razorpay_payment_id": "pay_real_456",
                    "razorpay_signature": valid_sig,
                    "email": email,
                    "plan": "monthly",
                },
            )
            self.assertEqual(valid_response.status_code, 200)
            self.assertTrue(valid_response.json()["is_pro"])
            self.assertEqual(database.get_user_subscription(email), "pro")
        finally:
            if self.orig_key_id:
                os.environ["RAZORPAY_KEY_ID"] = self.orig_key_id
            if self.orig_key_secret:
                os.environ["RAZORPAY_KEY_SECRET"] = self.orig_key_secret

    def test_roast_unlocked_for_pro_user(self):
        """Pro users receive untruncated issues in GET /api/roast/{id}."""
        issues = [
            {
                "quoted_text": f"text {i}",
                "category": "no-metrics",
                "roast": f"roast {i}",
                "fix": f"fix {i}",
                "start_offset": 0,
                "end_offset": 5,
                "severity_rank": i,
            }
            for i in range(1, 6)
        ]
        roast_id = database.save_roast(
            overall_score=45,
            band="mid",
            one_line_verdict="Verdict test",
            issues=issues,
            strengths=["Strength 1"],
            device_fingerprint="test-fp",
        )

        # Check standard free call: is_truncated is True, issues length is 3
        free_resp = self.client.get(f"/api/roast/{roast_id}")
        self.assertEqual(free_resp.status_code, 200)
        self.assertTrue(free_resp.json()["is_truncated"])
        self.assertEqual(len(free_resp.json()["issues"]), 3)
        self.assertEqual(free_resp.json()["total_issues"], 5)

        # Setup pro user and test with email
        email = "verified_pro_user@example.com"
        database.create_or_get_user(email)
        database.update_subscription(email, "pro")

        # Query with email param
        pro_resp = self.client.get(f"/api/roast/{roast_id}?email={email}")
        self.assertEqual(pro_resp.status_code, 200)
        self.assertFalse(pro_resp.json()["is_truncated"])
        self.assertEqual(len(pro_resp.json()["issues"]), 5)

        # Query with X-User-Email header
        pro_header_resp = self.client.get(f"/api/roast/{roast_id}", headers={"X-User-Email": email})
        self.assertEqual(pro_header_resp.status_code, 200)
        self.assertFalse(pro_header_resp.json()["is_truncated"])
        self.assertEqual(len(pro_header_resp.json()["issues"]), 5)

    def test_usage_pro_user(self):
        """GET /api/usage returns is_pro=True and unlimited remaining for Pro user."""
        email = "pro_usage_checker@example.com"
        database.create_or_get_user(email)
        database.update_subscription(email, "pro")

        resp = self.client.get(f"/api/usage?email={email}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_pro"])
        self.assertEqual(data["remaining"], 999999)

    def test_razorpay_webhook_signature_and_upgrade(self):
        """Webhook verifies HMAC signature and upgrades user to Pro."""
        os.environ["RAZORPAY_WEBHOOK_SECRET"] = "whsec_test123"
        webhook_email = "webhook_paid_user@example.com"

        try:
            payload = {
                "event": "payment.captured",
                "payload": {
                    "payment": {
                        "entity": {
                            "id": "pay_hook_999",
                            "email": webhook_email,
                            "amount": 29900,
                        }
                    }
                }
            }
            body_bytes = json.dumps(payload).encode("utf-8")

            # Missing signature should 400
            resp_missing = self.client.post("/api/billing/webhook", content=body_bytes)
            self.assertEqual(resp_missing.status_code, 400)

            # Invalid signature should 400
            resp_invalid = self.client.post(
                "/api/billing/webhook",
                content=body_bytes,
                headers={"X-Razorpay-Signature": "invalid_sig"},
            )
            self.assertEqual(resp_invalid.status_code, 400)

            # Valid signature should 200 and upgrade user
            valid_sig = hmac.new("whsec_test123".encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()
            resp_valid = self.client.post(
                "/api/billing/webhook",
                content=body_bytes,
                headers={"X-Razorpay-Signature": valid_sig},
            )
            self.assertEqual(resp_valid.status_code, 200)
            self.assertEqual(resp_valid.json()["status"], "received")

            # Confirm database has pro status
            self.assertEqual(database.get_user_subscription(webhook_email), "pro")
        finally:
            os.environ["RAZORPAY_WEBHOOK_SECRET"] = ""


if __name__ == "__main__":
    unittest.main()
