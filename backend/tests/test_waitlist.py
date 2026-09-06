"""
Unit tests for Pro Waitlist API, deduplication, validation, and storage.
"""
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.db import database


class TestWaitlist(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Clear in-memory waitlist cache for test isolation
        database._waitlist_memory.clear()

    def test_waitlist_join_success(self):
        """Test joining the Pro waitlist with a fresh email."""
        resp = self.client.post(
            "/api/waitlist/join",
            json={
                "email": "earlybird@example.com",
                "source": "pricing_pro_card",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "joined")
        self.assertFalse(data["is_already_on_list"])
        self.assertEqual(data["email"], "earlybird@example.com")
        self.assertIn("🎉", data["message"])

    def test_waitlist_graceful_deduplication(self):
        """Test that submitting the same email twice gracefully acknowledges duplicate."""
        # 1st submission
        r1 = self.client.post(
            "/api/waitlist/join",
            json={"email": "repeat@example.com", "source": "issue_card_locked"},
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()["status"], "joined")
        self.assertFalse(r1.json()["is_already_on_list"])

        # 2nd submission (should not error, returns already_joined status)
        r2 = self.client.post(
            "/api/waitlist/join",
            json={"email": "Repeat@Example.com", "source": "pricing_cta"},
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json()["status"], "already_joined")
        self.assertTrue(r2.json()["is_already_on_list"])
        self.assertIn("already on the list", r2.json()["message"])

    def test_waitlist_invalid_email(self):
        """Invalid email formats return 422 validation error."""
        invalid_emails = ["not-an-email", "@missing.com", "spaces in@email.com", ""]
        for bad_email in invalid_emails:
            resp = self.client.post(
                "/api/waitlist/join",
                json={"email": bad_email},
            )
            self.assertEqual(resp.status_code, 422)

    def test_waitlist_user_id_linking(self):
        """When an existing user signs up for the waitlist, their user_id is linked."""
        user = database.create_or_get_user("existing_user@example.com")
        user_id = user["id"]

        resp = self.client.post(
            "/api/waitlist/join",
            json={
                "email": "existing_user@example.com",
                "source": "daily_limit_reached",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "joined")

        # Verify in database memory
        record, _ = database.add_to_waitlist("existing_user@example.com")
        self.assertEqual(record.get("user_id"), user_id)

    def test_waitlist_stats_endpoint(self):
        """GET /api/waitlist/stats returns correct count."""
        self.client.post("/api/waitlist/join", json={"email": "user1@example.com"})
        self.client.post("/api/waitlist/join", json={"email": "user2@example.com"})

        resp = self.client.get("/api/waitlist/stats")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(resp.json()["total_waitlist"], 2)


if __name__ == "__main__":
    unittest.main()
