"""
Tests for Temporal Guard and Current Real-World Date Awareness.
Prevents false 'time machine' or 'future date' hallucinations when resumes
contain current or valid historical dates (e.g. 2026, 2025, 2024).
"""
import unittest
from datetime import datetime

from app.services.ai_analyzer import _validate_temporal_accuracy
from app.prompts import get_system_prompt, get_user_prompt_template


class TestTemporalGuard(unittest.TestCase):
    def test_drops_false_temporal_hallucination_for_current_year(self):
        """
        Server guard must drop hallucinated future/time-machine roasts
        when quoted dates are <= current year.
        """
        current_year = datetime.now().year
        data = {
            "overall_score": 68,
            "band": "mid",
            "one_line_verdict": "Bhai resume mein time machine wali dates kahan se aa gayi? 🕰️",
            "issues": [
                {
                    "quoted_text": f"Thiranex Aug {current_year} – Sep {current_year}",
                    "category": "other",
                    "badge_label": "FUTURE MEIN INTERNSHIP",
                    "roast": f"Aug {current_year} mein internship kar bhi li ya future se resume forward kar rahe ho? 🚀 Year check karo apna.",
                    "fix": "Year theek karo.",
                    "start_offset": 0,
                    "end_offset": 30,
                    "severity_rank": 1,
                },
                {
                    "quoted_text": "Reduced query latency by 45%",
                    "category": "no-metrics",
                    "badge_label": "PROOF DE DO",
                    "roast": "Kaam acha hai par thoda clarify karo.",
                    "fix": "Add details.",
                    "start_offset": 35,
                    "end_offset": 60,
                    "severity_rank": 2,
                }
            ],
            "strengths": ["Education crisp hai"]
        }

        _validate_temporal_accuracy(data, language="hi-IN")

        # The false temporal issue must be dropped
        self.assertEqual(len(data["issues"]), 1)
        self.assertEqual(data["issues"][0]["quoted_text"], "Reduced query latency by 45%")

        # The one-line verdict must be sanitized away from 'time machine'
        self.assertNotIn("time machine", data["one_line_verdict"].lower())
        self.assertNotIn("future", data["one_line_verdict"].lower())

    def test_keeps_legitimate_future_date_roast_for_absurd_year(self):
        """
        If candidate claims experience in year 2099, it IS an actual absurdity
        and should NOT be dropped.
        """
        data = {
            "overall_score": 30,
            "band": "weak",
            "one_line_verdict": "Ye kya hai bhai 😅",
            "issues": [
                {
                    "quoted_text": "TechCorp Jan 2099 – Dec 2099",
                    "category": "other",
                    "badge_label": "FUTURE DATE",
                    "roast": "2099 mein job kar li? Future se aaye ho kya?",
                    "fix": "Correct the year.",
                }
            ],
            "strengths": []
        }

        _validate_temporal_accuracy(data, language="hi-IN")
        self.assertEqual(len(data["issues"]), 1)

    def test_preserves_standard_student_prospective_graduation(self):
        """
        Students graduating in 2-3 years (e.g. B.Tech 2024-2028) must not
        be flagged with false time travel roasts.
        """
        current_year = datetime.now().year
        grad_year = current_year + 2
        data = {
            "overall_score": 60,
            "band": "mid",
            "one_line_verdict": "Time travel chal raha hai 🕰️",
            "issues": [
                {
                    "quoted_text": f"B.Tech Computer Science 2024 – {grad_year}",
                    "category": "other",
                    "badge_label": "FUTURE MEIN DEGREE",
                    "roast": f"{grad_year} mein degree complete ho gayi? Time machine lagayi hai kya?",
                    "fix": "Expected graduation likho.",
                }
            ],
            "strengths": []
        }

        _validate_temporal_accuracy(data, language="hi-IN")
        self.assertEqual(len(data["issues"]), 0)


class TestTemporalPrompts(unittest.TestCase):
    def test_system_prompt_has_current_date(self):
        now = datetime.now()
        month_year = now.strftime("%B %Y")
        current_year = str(now.year)

        sys_prompt_hi = get_system_prompt("hi-IN")
        self.assertIn(month_year, sys_prompt_hi)
        self.assertIn(current_year, sys_prompt_hi)

        sys_prompt_en = get_system_prompt("en")
        self.assertIn(month_year, sys_prompt_en)
        self.assertIn(current_year, sys_prompt_en)

    def test_user_prompt_template_has_current_date(self):
        now = datetime.now()
        month_year = now.strftime("%B %Y")

        user_template_hi = get_user_prompt_template("hi-IN")
        self.assertIn(month_year, user_template_hi)
        # Verify that .format() can still be called with resume_text and exclusion_block
        formatted = user_template_hi.format(
            resume_text="Sample Resume",
            exclusion_block="",
        )
        self.assertIn("Sample Resume", formatted)
        self.assertIn(month_year, formatted)
