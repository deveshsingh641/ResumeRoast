"""
Automated QA & Error-Handling Edge Case Test Suite for Resume Roast (unittest + pytest compatible).
"""
import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.db import database
from app.services import extractor


class TestResumeRoastEdgeCases(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_empty_file_upload_rejected(self):
        """Empty 0-byte file must be rejected with 422 immediately."""
        files = {"file": ("empty.pdf", b"", "application/pdf")}
        response = self.client.post("/api/roast", files=files)
        self.assertEqual(response.status_code, 422)
        self.assertIn("empty", response.json()["detail"].lower())

    def test_fake_pdf_magic_bytes_rejected(self):
        """A text file or image renamed to .pdf must be rejected via magic bytes check."""
        fake_pdf_bytes = b"Hello world, I am just a plain text file pretending to be a PDF!"
        files = {"file": ("fake_resume.pdf", fake_pdf_bytes, "application/pdf")}
        response = self.client.post("/api/roast", files=files)
        self.assertEqual(response.status_code, 422)
        self.assertIn("not appear to be a valid pdf", response.json()["detail"].lower())

    def test_fake_docx_rejected(self):
        """A fake file renamed to .docx must be rejected."""
        fake_docx_bytes = b"Not a real docx zip archive"
        files = {"file": ("fake_resume.docx", fake_docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
        response = self.client.post("/api/roast", files=files)
        self.assertEqual(response.status_code, 422)
        self.assertIn("not appear to be a valid word document", response.json()["detail"].lower())

    def test_file_over_5mb_rejected(self):
        """File over 5MB must be rejected with 413."""
        oversized_bytes = b"%PDF-" + b"0" * (5 * 1024 * 1024 + 100)
        files = {"file": ("huge_resume.pdf", oversized_bytes, "application/pdf")}
        response = self.client.post("/api/roast", files=files)
        self.assertEqual(response.status_code, 413)
        self.assertIn("too large", response.json()["detail"].lower())

    def test_offset_mapping_with_paraphrased_or_missing_text(self):
        """Offset mapping must never crash on paraphrased/missing substrings."""
        full_text = "Experienced Senior Software Engineer who led frontend modernization."
        quoted_texts = [
            "led frontend modernization",
            "Non-existent text that model hallucinated",
            "",
        ]
        offsets = extractor.map_quoted_text_to_offsets(quoted_texts, full_text)
        self.assertEqual(len(offsets), 3)
        self.assertIsNotNone(offsets[0][0])
        self.assertEqual(offsets[1], (None, None))
        self.assertEqual(offsets[2], (None, None))

    def test_expired_roast_cleanup(self):
        """Expired anonymous roasts (older than 7 days) must be purged."""
        roast_id = database.save_roast(
            overall_score=40,
            band="weak",
            one_line_verdict="Test verdict",
            issues=[],
            strengths=[],
        )
        record = database.get_roast(roast_id)
        self.assertIsNotNone(record)

        database._memory_store[roast_id]["expires_at"] = "2020-01-01T00:00:00"
        cleaned = database.cleanup_expired_roasts()
        self.assertGreaterEqual(cleaned, 1)
        self.assertIsNone(database.get_roast(roast_id))

    def test_404_on_nonexistent_roast(self):
        """Fetching unknown ID returns clean 404 with friendly message."""
        response = self.client.get("/api/roast/00000000-0000-0000-0000-000000000000")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"].lower())

    def test_health_check_endpoint(self):
        """Health check endpoint must return 200 OK with service identifier."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_usage_endpoint(self):
        """Usage endpoint returns remaining free tier count."""
        response = self.client.get("/api/usage")
        self.assertEqual(response.status_code, 200)
        self.assertIn("remaining", response.json())
        self.assertIn("limit", response.json())

    def test_checkout_endpoint(self):
        """Checkout endpoint initializes checkout session or simulation."""
        response = self.client.post(
            "/api/checkout",
            json={"email": "candidate@example.com", "plan": "monthly"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("url", response.json())

    def test_webhook_missing_signature_rejected(self):
        """Webhook endpoint rejects requests missing Stripe-Signature header with 400."""
        response = self.client.post("/api/webhook", content=b"{}")
        self.assertEqual(response.status_code, 400)
        self.assertIn("signature", response.json()["detail"].lower())

    def test_cancel_subscription(self):
        """Cancelling subscription updates status cleanly."""
        response = self.client.post(
            "/api/subscription/cancel",
            json={"email": "candidate@example.com"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "cancelled")

    def test_hinglish_tone_detection(self):
        """Hinglish tone helper detects WhatsApp-style Hinglish markers."""
        from app.services.ai_analyzer import _has_hinglish_tone
        self.assertTrue(_has_hinglish_tone("Bhai resume hai ya suspense novel? 🕵️"))
        self.assertTrue(_has_hinglish_tone("\"Responsible for\" likhna band karo yaar 😩 recruiter ko number chahiye"))
        self.assertTrue(_has_hinglish_tone("Dum hai boss, bas thoda masala kam hai 🍛"))
        self.assertFalse(_has_hinglish_tone("This candidate has extensive experience in software development."))

    def test_validate_schema_rejects_pure_english_tone(self):
        """Schema validation rejects responses lacking Hinglish persona markers."""
        from app.services.ai_analyzer import _validate_schema
        english_data = {
            "overall_score": 50,
            "band": "mid",
            "one_line_verdict": "This is a standard software engineering resume.",
            "issues": [
                {
                    "quoted_text": "Responsible for backend architecture",
                    "category": "no-metrics",
                    "roast": "This bullet point lacks concrete statistical metrics.",
                    "fix": "Add numbers to quantify your work.",
                }
            ],
            "strengths": ["Clean layout"],
        }
        with self.assertRaises(ValueError) as ctx:
            _validate_schema(english_data)
        self.assertIn("Hinglish", str(ctx.exception))

    def test_validate_schema_accepts_hinglish_roast(self):
        """Schema validation accepts valid Hinglish roasts with concrete fixes."""
        from app.services.ai_analyzer import _validate_schema
        hinglish_data = {
            "overall_score": 34,
            "band": "weak",
            "one_line_verdict": "Bhai resume hai ya suspense novel? 🕵️",
            "issues": [
                {
                    "quoted_text": "Responsible for building UI components",
                    "category": "no-metrics",
                    "roast": "\"Responsible for\" likhna band karo yaar 😩 recruiter ko number chahiye, kahani nahi.",
                    "fix": "Built 12 reusable UI components, cutting page load time by 30%.",
                }
            ],
            "strengths": ["Formatting clean hai, ATS ko padhne mein dikkat nahi hogi 👍"],
        }
        _validate_schema(hinglish_data, "Responsible for building UI components and APIs")
        self.assertEqual(hinglish_data["band"], "weak")

    def test_fallback_roast_generator_persona(self):
        """Fallback roast generator produces rich Hinglish roasts and proper schema."""
        from app.services.ai_analyzer import _generate_fallback_roast, _validate_schema
        sample_resume = (
            "John Doe\n"
            "Software Engineer\n"
            "Responsible for building web features\n"
            "Worked closely with cross-functional teams\n"
            "Hobbies: Playing cricket, listening to music\n"
            "Declaration: I hereby declare everything is accurate"
        )
        fallback_data = _generate_fallback_roast(sample_resume)
        self.assertIn("overall_score", fallback_data)
        self.assertIn("band", fallback_data)
        self.assertIn("one_line_verdict", fallback_data)
        self.assertGreaterEqual(len(fallback_data["issues"]), 1)
        _validate_schema(fallback_data, sample_resume)

    def test_voice_note_generation_and_stream(self):
        """Voice note script is generated and audio endpoint serves media."""
        from app.services import voice_service
        script = voice_service.build_voice_roast_script(
            one_line_verdict="Bhai resume hai ya suspense novel? 🕵️",
            issues=[{"roast": "Responsible for likhna band karo yaar"}],
            overall_score=34,
        )
        self.assertIn("score", script.lower())
        self.assertNotIn("🕵️", script)

        # Save test roast in DB
        roast_id = database.save_roast(
            overall_score=34,
            band="weak",
            one_line_verdict="Bhai resume hai ya suspense novel? 🕵️",
            issues=[{"quoted_text": "Responsible for...", "category": "no-metrics", "roast": "Responsible for likhna band karo yaar", "fix": "Add metrics"}],
            strengths=["Clean formatting"],
        )
        resp = self.client.post(f"/api/roast/{roast_id}/voice")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("audio_url", resp.json())
        self.assertIn("disclaimer", resp.json())

        # Stream audio
        audio_resp = self.client.get(f"/api/roast/{roast_id}/voice/audio")
        self.assertEqual(audio_resp.status_code, 200)
        self.assertIn("audio", audio_resp.headers["content-type"])

    def test_battle_endpoint(self):
        """Roast battle compares two resumes and declares winner."""
        import io
        from docx import Document

        def _make_docx(text: str) -> bytes:
            doc = Document()
            for p in text.split("\n"):
                doc.add_paragraph(p)
            buf = io.BytesIO()
            doc.save(buf)
            return buf.getvalue()

        f1_text = (
            "Senior Backend Engineer with 6 years experience.\n"
            "Led architecture of high-scale payment microservices across 15 services.\n"
            "Reduced latency by 45% and improved database throughput by 200% handling 50k requests per minute.\n"
            "Proficient in Python, Go, PostgreSQL, Redis, Kubernetes, Docker, and AWS."
        )
        f2_text = (
            "Junior Web Developer seeking entry level role.\n"
            "Responsible for assisting senior team members with various frontend duties.\n"
            "Worked closely with designers to make UI components and fixes.\n"
            "Hobbies: Playing cricket, video games, listening to music.\n"
            "Declaration: I hereby declare everything is true to my knowledge."
        )

        f1_bytes = _make_docx(f1_text)
        f2_bytes = _make_docx(f2_text)

        files = {
            "fighter1": ("resume1.docx", f1_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            "fighter2": ("resume2.docx", f2_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        }
        resp = self.client.post("/api/battle", files=files)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("winner", data)
        self.assertIn("margin", data)
        self.assertIn("verdict", data)
        self.assertIn("fighter_1", data)
        self.assertIn("fighter_2", data)

        # Fetch stored battle
        battle_id = data["id"]
        get_resp = self.client.get(f"/api/battle/{battle_id}")
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json()["id"], battle_id)

    def test_wall_anonymization_and_feed(self):
        """Wall of Shame/Fame sanitizes PII and returns paginated feed."""
        from app.services import wall_service
        raw_text = "Senior Dev at Google, email: john.doe@gmail.com, phone: +91 9876543210 from IIT Bombay"
        sanitized = wall_service.anonymize_text(raw_text)
        self.assertNotIn("john.doe@gmail.com", sanitized)
        self.assertNotIn("9876543210", sanitized)
        self.assertIn("[Email]", sanitized)
        self.assertIn("[Org]", sanitized)

        # Publish roast
        roast_id = database.save_roast(
            overall_score=28,
            band="weak",
            one_line_verdict="Suspense novel by john.doe@gmail.com at Google 😭",
            issues=[{"quoted_text": "Did work", "category": "no-metrics", "roast": "Google engineer with no numbers", "fix": "Add metrics"}],
            strengths=["Clean formatting"],
        )
        pub_resp = self.client.post("/api/wall/publish", json={"roast_id": roast_id})
        self.assertEqual(pub_resp.status_code, 200)
        self.assertEqual(pub_resp.json()["type"], "shame")
        wall_id = pub_resp.json()["wall_id"]

        # Check feed
        feed_resp = self.client.get("/api/wall?type=shame&sort=recent")
        self.assertEqual(feed_resp.status_code, 200)
        self.assertGreaterEqual(feed_resp.json()["total"], 1)

        # Flag entry
        flag_resp = self.client.post(f"/api/wall/{wall_id}/flag")
        self.assertEqual(flag_resp.status_code, 200)
        self.assertEqual(flag_resp.json()["status"], "flagged")

    def test_find_duplicate_roasts_and_deduplication(self):
        """Pairwise duplicate detection identifies >85% similar roast lines and substitutes varied phrasing."""
        from app.services.ai_analyzer import _find_duplicate_roasts, _deduplicate_roasts

        duplicate_issues = [
            {
                "quoted_text": "Responsible for API endpoints",
                "category": "no-metrics",
                "roast": "Is line mein ek bhi number nahi hai bhai! Recruiter ko kaise pata chalega kitna kaam kiya? 📉",
                "fix": "Add numbers",
            },
            {
                "quoted_text": "Responsible for database queries",
                "category": "no-metrics",
                "roast": "Is line mein ek bhi number nahi hai bhai! Recruiter ko kaise pata chalega kitna kaam kiya? 📉",
                "fix": "Add numbers",
            },
            {
                "quoted_text": "Worked closely with engineers",
                "category": "buzzword",
                "roast": "Worked closely with — matlab kya kiya bhai? Chai piya ya kaam bhi kiya ☕",
                "fix": "Be specific",
            },
        ]

        dups = _find_duplicate_roasts(duplicate_issues)
        self.assertEqual(len(dups), 1)
        self.assertEqual(dups[0][0], 1)  # Index 1 is the duplicate

        data = {"issues": duplicate_issues}
        _deduplicate_roasts(data)
        self.assertNotEqual(data["issues"][0]["roast"], data["issues"][1]["roast"])
        self.assertEqual(len(_find_duplicate_roasts(data["issues"])), 0)


if __name__ == "__main__":
    unittest.main()
