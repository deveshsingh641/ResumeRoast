"""
Unit & Integration tests for Job Description (JD) Match Mode & ATS Reality Check.
"""
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.db import database


class TestJDMatch(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_sample_jds(self):
        """GET /api/match/samples returns curated tech JDs."""
        resp = self.client.get("/api/match/samples")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertGreaterEqual(len(data["samples"]), 3)
        sample_ids = [s["id"] for s in data["samples"]]
        self.assertIn("swiggy-frontend", sample_ids)
        self.assertIn("zerodha-backend", sample_ids)

    def test_post_match_json_free_tier_truncation(self):
        """POST /api/match with JSON body performs analysis and truncates for free tier."""
        resume_sample = """
        Rahul Verma
        Frontend Developer
        Skills: HTML, CSS, JavaScript, Basic React
        Experience:
        - Worked on company landing page redesign.
        - Fixed small bugs in frontend repository.
        Declaration: All info is true.
        Hobbies: Cricket, traveling.
        """
        jd_sample = """
        Frontend Engineer II at Swiggy
        Requirements:
        - Deep experience with React, TypeScript, Next.js, and Zustand.
        - Knowledge of Kubernetes, Docker, and CI/CD pipelines.
        - Optimizing Web Vitals and render performance.
        - Automated testing with Jest and Playwright.
        """
        resp = self.client.post(
            "/api/match",
            json={
                "resume_text": resume_sample,
                "job_description": jd_sample,
                "job_title": "Frontend Engineer II",
                "company_name": "Swiggy",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("match_score", data)
        self.assertIn(data["ats_status"], ["rejected", "borderline", "shortlisted"])
        self.assertTrue(len(data["verdict"]) > 0)
        self.assertIn("matched_skills", data)
        self.assertIn("missing_keywords", data)
        # Verify free tier truncation
        self.assertTrue(data["is_truncated"])
        self.assertLessEqual(len(data["missing_keywords"]), 2)
        self.assertGreaterEqual(data["total_missing_keywords"], 2)
        self.assertLessEqual(len(data["tailored_bullet_rewrites"]), 1)

    def test_post_match_pro_user_unlocked(self):
        """Pro users receive full keyword matrix without truncation."""
        resume_sample = """
        Anjali Rao
        Full Stack Engineer
        Skills: React, Node.js, Python, PostgreSQL, Docker
        Experience:
        - Built scalable web dashboard with React and Node.js.
        - Deployed microservices using Docker and AWS.
        """
        jd_sample = """
        Core Backend Engineer at Zerodha
        Requirements:
        - Go (Golang), PostgreSQL, Redis, Kafka, Kubernetes, Microservices.
        - Low-latency query tuning, ACID guarantees, and distributed systems.
        """
        # Set Pro user in database
        from app.services.pro_auth import create_pro_token
        database.create_or_get_user("pro_tester@example.com")
        database.update_subscription("pro_tester@example.com", "pro")

        # 1. Unauthenticated claim via header must NOT grant Pro access
        unauth_resp = self.client.post(
            "/api/match",
            headers={"x-user-email": "pro_tester@example.com"},
            json={
                "resume_text": resume_sample,
                "job_description": jd_sample,
            },
        )
        self.assertEqual(unauth_resp.status_code, 200)
        self.assertFalse(unauth_resp.json()["is_pro"])

        # 2. Authenticated claim via cryptographic X-Pro-Token unlocks Pro
        token = create_pro_token("pro_tester@example.com")
        resp = self.client.post(
            "/api/match",
            headers={"X-Pro-Token": token},
            json={
                "resume_text": resume_sample,
                "job_description": jd_sample,
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["is_pro"])
        self.assertFalse(data["is_truncated"])
        self.assertGreaterEqual(len(data["missing_keywords"]), 2)

    def test_post_match_short_jd_validation_error(self):
        """Short or missing job description returns 422."""
        resp = self.client.post(
            "/api/match",
            json={
                "resume_text": "Experienced software engineer with 5 years in Python.",
                "job_description": "Too short",
            },
        )
        self.assertEqual(resp.status_code, 422)
        self.assertIn("Job Description", resp.json()["detail"])

    def test_post_match_missing_resume_validation_error(self):
        """Missing resume returns 422."""
        resp = self.client.post(
            "/api/match",
            json={
                "job_description": "We are hiring a Lead Backend Engineer with 5+ years experience in Go and Distributed Systems.",
            },
        )
        self.assertEqual(resp.status_code, 422)

    def test_post_match_with_roast_id(self):
        """POST /api/match with roast_id uses saved resume_text from existing roast."""
        roast_id = database.save_roast(
            overall_score=45,
            band="weak",
            one_line_verdict="Good potential but needs more concrete metrics.",
            issues=[],
            strengths=[],
            resume_text="""
            Siddharth Rao - Frontend Engineer
            Skills: HTML5, CSS3, JavaScript, React.js, Redux, Git
            Experience: Built user dashboard with React and handled state management.
            """,
        )

        resp = self.client.post(
            "/api/match",
            json={
                "roast_id": roast_id,
                "job_description": """
                Senior Frontend Engineer at Swiggy
                Requirements: React, TypeScript, Next.js, Redux Toolkit, Web Vitals, Jest testing.
                """,
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("match_score", data)
        self.assertIn("React.js", data["matched_skills"])

    def test_post_match_multipart_upload(self):
        """POST /api/match with multipart file upload processes resume correctly."""
        import io
        from reportlab.pdfgen import canvas

        buf = io.BytesIO()
        c = canvas.Canvas(buf)
        c.drawString(50, 750, "Aarav Sharma - Go Backend Engineer")
        c.drawString(50, 730, "Skills: Go, Golang, PostgreSQL, Docker, Redis, Microservices")
        c.drawString(50, 710, "Experience: Engineered financial transaction APIs handling high throughput.")
        c.save()
        pdf_bytes = buf.getvalue()

        resp = self.client.post(
            "/api/match",
            files={"file": ("aarav_resume.pdf", pdf_bytes, "application/pdf")},
            data={
                "job_description": """
                Core Trading Backend SDE at Zerodha
                Requirements:
                - 2+ years backend engineering with Go (Golang), PostgreSQL, Redis, Kafka.
                - Microservices with gRPC and high-throughput systems.
                """,
                "job_title": "Backend SDE",
                "company_name": "Zerodha",
            },
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("match_score", data)
        self.assertEqual(data["company_name"], "Zerodha")


if __name__ == "__main__":
    unittest.main()
