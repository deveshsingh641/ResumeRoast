"""
Regression test: server-side no-metrics guard must never let a
"no-metrics" category through when quoted_text already contains a number.

This validates _validate_no_metrics_categorization() directly — no live AI
call needed, making the test fast and fully deterministic.
"""
from __future__ import annotations

import unittest

# Inline import to test the standalone function
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.ai_analyzer import _validate_no_metrics_categorization


def _make_data(quoted_text: str) -> dict:
    """Build a minimal response dict with a single no-metrics issue."""
    return {
        "overall_score": 42,
        "band": "mid",
        "one_line_verdict": "Ye test hai 🧪",
        "issues": [
            {
                "quoted_text": quoted_text,
                "category": "no-metrics",
                "roast": "Number nahi hai bhai.",
                "fix": "Add a number.",
                "start_offset": 0,
                "end_offset": len(quoted_text),
                "severity_rank": 1,
            }
        ],
        "strengths": [],
    }


class TestNoMetricsRegression(unittest.TestCase):
    """
    For each line that already contains a digit or number word,
    _validate_no_metrics_categorization() must drop the issue
    so that issues list is empty afterwards.
    """

    def _assert_dropped(self, quoted_text: str):
        data = _make_data(quoted_text)
        _validate_no_metrics_categorization(data)
        self.assertEqual(
            data["issues"],
            [],
            f"Expected issue to be dropped for numbered line: {quoted_text!r}",
        )

    def _assert_kept(self, quoted_text: str):
        data = _make_data(quoted_text)
        _validate_no_metrics_categorization(data)
        self.assertEqual(
            len(data["issues"]),
            1,
            f"Expected issue to be kept for unnumbered line: {quoted_text!r}",
        )

    # --- Lines WITH numbers — must ALL be dropped ---

    def test_line_with_digit_percent(self):
        self._assert_dropped("Improved server response time by 40%")

    def test_line_with_plain_digit(self):
        self._assert_dropped("Led a team of 5 engineers to ship the product")

    def test_line_with_large_number(self):
        self._assert_dropped("Handled 1,200 customer support tickets per quarter")

    def test_line_with_decimal(self):
        self._assert_dropped("Achieved 99.9% uptime across production services")

    def test_line_with_k_suffix(self):
        self._assert_dropped("Grew newsletter subscriber base to 12k users")

    def test_line_with_spelled_number_one(self):
        self._assert_dropped("Led one cross-functional squad to complete the migration")

    def test_line_with_spelled_number_three(self):
        self._assert_dropped("Managed three product launches simultaneously")

    def test_line_with_spelled_ordinal(self):
        self._assert_dropped("Received first place in the internal hackathon")

    def test_line_with_range_numbers(self):
        self._assert_dropped("Reduced load time from 3s to 0.8s")

    def test_line_with_year(self):
        self._assert_dropped("Worked at InfyTech from 2020 to 2022")

    # --- Lines WITHOUT numbers — must be kept (guard does NOT over-drop) ---

    def test_genuinely_no_metric_line(self):
        self._assert_kept("Responsible for handling client relationships")

    def test_genuinely_no_metric_line_2(self):
        self._assert_kept("Assisted in achieving sales targets")

    def test_genuinely_no_metric_line_vague(self):
        self._assert_kept("Collaborated with the design team to improve the product")

    def test_genuinely_no_metric_line_tools(self):
        self._assert_kept("Built backend services using Python and FastAPI")


if __name__ == "__main__":
    unittest.main()