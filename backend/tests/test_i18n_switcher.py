"""
Tests for Country-Based Language Switcher, Detection, Persona Selection,
Voice Note Scripting, and User Preference Storage.
"""
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.db import database
from app.i18n.mapping import (
    DEFAULT_LANGUAGE,
    HINGLISH_LANGUAGE,
    COUNTRY_TO_LANGUAGE,
    language_from_country,
    normalize_language,
    language_from_request,
)
from app.services.ai_analyzer import (
    analyze_resume,
    _generate_fallback_roast,
    _validate_schema,
    _validate_no_metrics_categorization,
)
from app.services.voice_service import (
    build_voice_roast_script,
    generate_voice_roast_audio,
)
from app.services.certificate_service import generate_certificate_pdf


class TestI18nSwitcher(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_country_mapping_table(self):
        """Test ISO country code to language mapping."""
        self.assertEqual(language_from_country("IN"), "hi-IN")
        self.assertEqual(language_from_country("US"), "en")
        self.assertEqual(language_from_country("GB"), "en")
        self.assertEqual(language_from_country("CA"), "en")
        self.assertEqual(language_from_country("DE"), "en")
        self.assertEqual(language_from_country("JP"), "en")
        self.assertEqual(language_from_country(None), "en")
        self.assertEqual(language_from_country(""), "en")
        self.assertEqual(language_from_country("XX"), "en")  # Cloudflare unknown
        self.assertEqual(language_from_country("T1"), "en")  # Tor

    def test_normalize_language(self):
        """Test language code normalization and aliases."""
        self.assertEqual(normalize_language("hi-IN"), "hi-IN")
        self.assertEqual(normalize_language("hi_IN"), "hi-IN")
        self.assertEqual(normalize_language("hi"), "hi-IN")
        self.assertEqual(normalize_language("en"), "en")
        self.assertEqual(normalize_language("en-US"), "en")
        self.assertEqual(normalize_language("en-gb"), "en")
        self.assertEqual(normalize_language("fr"), "en")  # Unsupported falls back to English
        self.assertEqual(normalize_language(""), "en")
        self.assertEqual(normalize_language(None), "en")

    def test_detect_endpoint_with_cf_country(self):
        """Test GET /api/i18n/detect with CF-IPCountry header."""
        # India header
        res = self.client.get("/api/i18n/detect", headers={"CF-IPCountry": "IN"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["country"], "IN")
        self.assertEqual(data["language"], "hi-IN")

        # US header
        res = self.client.get("/api/i18n/detect", headers={"CF-IPCountry": "US"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["country"], "US")
        self.assertEqual(data["language"], "en")

        # Query param override
        res = self.client.get("/api/i18n/detect?country=IN")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["country"], "IN")
        self.assertEqual(data["language"], "hi-IN")

        # No header
        res = self.client.get("/api/i18n/detect")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsNone(data["country"])
        self.assertEqual(data["language"], "en")

    def test_user_language_persistence(self):
        """Test saving and retrieving user's preferred language."""
        email = "multilang_user@example.com"
        # Initial state: None / default en
        res = self.client.get(f"/api/user/language?email={email}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["language"], "en")

        # Update to hi-IN
        res = self.client.post("/api/user/language", json={"email": email, "language": "hi-IN"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["ok"], True)
        self.assertEqual(res.json()["language"], "hi-IN")

        # Verify persisted
        res = self.client.get(f"/api/user/language?email={email}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["language"], "hi-IN")

        # Update back to en
        res = self.client.post("/api/user/language", json={"email": email, "language": "en"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["language"], "en")

        res = self.client.get(f"/api/user/language?email={email}")
        self.assertEqual(res.json()["language"], "en")

    def test_ai_analyzer_english_fallback(self):
        """Test that English fallback produces witty English critiques with no Hindi markers."""
        sample_resume = (
            "Alex Morgan\n"
            "Full Stack Software Engineer\n"
            "Responsible for designing reusable React components and microservices\n"
            "Worked closely with cross-functional teams to drive synergy\n"
            "Curriculum Vitae (Page 1 of 4)\n"
            "Declaration: All details are accurate to my knowledge\n"
            "Hobbies: Chess, Photography"
        )
        res = _generate_fallback_roast(sample_resume, language="en")
        self.assertIn("overall_score", res)
        self.assertIn("band", res)
        self.assertIn("one_line_verdict", res)
        self.assertGreaterEqual(len(res["issues"]), 2)

        # Ensure schema validates for English
        _validate_schema(res, sample_resume, language="en")

        # Check issues contain English wording
        issue_texts = " ".join([i["roast"] for i in res["issues"]])
        self.assertTrue(len(issue_texts) > 20)

    def test_ai_analyzer_hinglish_fallback(self):
        """Test that Hinglish fallback produces WhatsApp-style Hindi-English critiques."""
        sample_resume = (
            "Rohan Sharma\n"
            "Software Engineer\n"
            "Responsible for building scalable backend architecture in Python\n"
            "Hobbies: Cricket, traveling\n"
            "Declaration: Everything is true"
        )
        res = _generate_fallback_roast(sample_resume, language="hi-IN")
        self.assertIn("overall_score", res)
        _validate_schema(res, sample_resume, language="hi-IN")
        # Ensure at least one issue or verdict has Hinglish tone
        roasts = [i["roast"] for i in res["issues"]] + [res["one_line_verdict"]]
        from app.services.ai_analyzer import _has_hinglish_tone
        self.assertTrue(any(_has_hinglish_tone(r) for r in roasts))

    def test_no_metrics_validation_both_languages(self):
        """Test that no-metrics validation guard drops false claims in both languages."""
        # Line with number labeled no-metrics should be dropped
        bad_data = {
            "overall_score": 50,
            "band": "mid",
            "one_line_verdict": "Verdict",
            "issues": [
                {
                    "quoted_text": "Scaled throughput by 35% across 5 services",
                    "category": "no-metrics",
                    "roast": "Where are the numbers?",
                    "fix": "Add numbers",
                },
                {
                    "quoted_text": "Responsible for managing databases",
                    "category": "no-metrics",
                    "roast": "How many databases?",
                    "fix": "Quantify",
                },
            ],
            "strengths": ["Good formatting"],
        }
        _validate_no_metrics_categorization(bad_data)
        self.assertEqual(len(bad_data["issues"]), 1)
        self.assertEqual(bad_data["issues"][0]["quoted_text"], "Responsible for managing databases")

    def test_voice_script_english_vs_hinglish(self):
        """Test voice script generation in English vs Hinglish."""
        issues = [
            {"quoted_text": "Responsible for backend", "roast": "This line has zero metrics and pure vibes."},
            {"quoted_text": "Synergized deliverables", "roast": "Corporate buzzword overload."},
        ]
        # English
        en_script = build_voice_roast_script("Needs major work", issues, 35, language="en")
        self.assertTrue("Look, I just went through" in en_script or "Alright, here is" in en_script or "Okay, I just" in en_script)
        self.assertIn("First off:", en_script)
        self.assertIn("score", en_script.lower())

        # Hinglish
        hi_script = build_voice_roast_script("Bhai resume hai ya suspense novel?", issues, 35, language="hi-IN")
        self.assertTrue("Arre bhai" in hi_script or "Sun bhai" in hi_script or "Arey yaar" in hi_script)
        self.assertIn("Pehli baat:", hi_script)

    def test_demo_roast_endpoint_localization(self):
        """Test GET /api/roast/demo returns localized demo payload based on X-Language."""
        # Hinglish
        res_hi = self.client.get("/api/roast/demo", headers={"X-Language": "hi-IN"})
        self.assertEqual(res_hi.status_code, 200)
        data_hi = res_hi.json()
        self.assertIn("Bhai", data_hi["one_line_verdict"])

        # English
        res_en = self.client.get("/api/roast/demo", headers={"X-Language": "en"})
        self.assertEqual(res_en.status_code, 200)
        data_en = res_en.json()
        self.assertIn("mystery novel", data_en["one_line_verdict"])
        self.assertEqual(data_en["overall_score"], 28)

    def test_voice_demo_endpoint_localization(self):
        """Test POST /api/roast/demo/voice returns localized script and audio link."""
        # English demo voice note
        res_en = self.client.post("/api/roast/demo/voice", headers={"X-Language": "en"})
        self.assertEqual(res_en.status_code, 200)
        data_en = res_en.json()
        self.assertIn("script", data_en)
        self.assertTrue("Look, I" in data_en["script"] or "Alright" in data_en["script"] or "Okay" in data_en["script"])
        self.assertIn("lang=en", data_en["audio_url"])

        # Hinglish demo voice note
        res_hi = self.client.post("/api/roast/demo/voice", headers={"X-Language": "hi-IN"})
        self.assertEqual(res_hi.status_code, 200)
        data_hi = res_hi.json()
        self.assertIn("script", data_hi)
        self.assertTrue("Arre bhai" in data_hi["script"] or "Sun bhai" in data_hi["script"] or "Arey yaar" in data_hi["script"])
        self.assertIn("lang=hi-IN", data_hi["audio_url"])


if __name__ == "__main__":
    unittest.main()
