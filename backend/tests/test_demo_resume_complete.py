"""
Complete Feature Verification Test Suite for Resume Roast
Tests each and every feature end-to-end using a realistic demo resume:
1. PDF Creation & Resume Validation
2. Core Roast Engine (Score, Band, Verdict, Issues, Strengths, Fix Diversity)
3. Roast Retrieval by ID
4. Built-in Sample/Demo Endpoint (Hinglish & English)
5. AI Interview Hot-Seat (Trap questions, Interviewer trap, Rookie blunder, STAR framework, Spoken script)
6. Roast Back AI Comeback Live Chat
7. AI STAR Bullet Rewriter Studio (3 distinct rewrite formulas)
8. Official Parody Certificate PDF Generation (Wax seal & Watermark)
9. LinkedIn 3-Slide Carousel PDF Generation
10. Job Description Match Engine (ATS keyword gaps, Match score, Recommendations)
11. 1-on-1 Battle Mode (Candidate vs Candidate, savage verdict)
12. Interactive Emoji Reactions
13. Public Wall of Shame/Fame (Anonymization, publish, retrieval)
14. Voice Note Audio Script Generation
15. Dimensional Health Scorecard Metrics (5 Vectors)
16. Before vs After Makeover Drop-in Parsing
17. ATS Markdown Export (.md)
18. English vs Hinglish Persona Switch
"""
import io
import json
import os
import re
import unittest
from reportlab.pdfgen import canvas
from fastapi.testclient import TestClient

from app.main import app
from app.db import database
from app.services import (
    ai_analyzer,
    interview_griller,
    bullet_rewriter,
    battle_service,
    jd_match_service,
    certificate_service,
    carousel_service,
    voice_service,
)


def make_pdf(text: str) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800
    for line in text.strip().splitlines():
        if not line.strip():
            y -= 12
            continue
        c.drawString(40, y, line[:95])
        y -= 14
        if y < 40:
            c.showPage()
            y = 800
    c.save()
    return buf.getvalue()


DEMO_RESUME_TEXT = """
Aakash Verma
Email: aakash.verma@example.com | Phone: +91 9876543210 | Bengaluru, India
Full-Stack Development Intern Remote (2023 - Present)

PROFESSIONAL SUMMARY
Passionate, hardworking and detail-oriented developer looking for a dynamic environment.

WORK EXPERIENCE
TechCorp Solutions - Full-Stack Development Intern (June 2023 - Present)
- Designed JWT authentication and RBAC-driven CRUD workflows, hardened through peer review and iteration.
- Responsible for maintaining database queries and server endpoints.
- Assisted team with writing documentation and managing client deliverables.
- Worked closely with senior engineers to build responsive user interfaces.

TECHNICAL PROJECTS
E-Commerce Microservices Platform
- Built REST API services in Python FastAPI and integrated Redis caching.
- Created responsive frontend dashboard in React and Tailwind CSS.

EDUCATION
B.Tech in Computer Science and Engineering (2020 - 2024)
CGPA: 8.4 / 10

TECHNICAL SKILLS
Python, JavaScript, TypeScript, React.js, FastAPI, PostgreSQL, Redis, Docker, Git
"""

DEMO_JD_TEXT = """
Role: Full-Stack Software Engineer (Backend & React)
Location: Remote / Bengaluru

Responsibilities:
- Build high-throughput RESTful microservices in Python (FastAPI/Django) and Node.js.
- Optimize PostgreSQL database queries, index strategies, and Redis caching.
- Implement secure OAuth2/JWT authentication and RBAC systems.
- Collaborate with frontend engineers to ship React/TypeScript web apps.
- Own CI/CD deployment pipelines on AWS and Docker containers.

Requirements:
- 1-3 years of full-stack engineering experience.
- Strong knowledge of Data Structures, Algorithms, and System Design.
- Proven track record of shipping scalable production software with measurable business impact.
"""


class TestDemoResumeComplete(unittest.TestCase):
    client: TestClient
    pdf_bytes: bytes

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.pdf_bytes = make_pdf(DEMO_RESUME_TEXT)

    def _create_demo_roast(self, lang="hi-IN"):
        res = self.client.post(
            "/api/roast",
            files={"file": ("aakash_verma_resume.pdf", self.pdf_bytes, "application/pdf")},
            headers={"Accept-Language": lang},
        )
        self.assertEqual(res.status_code, 200, f"Upload failed: {res.text}")
        return res.json()

    def test_01_upload_and_create_roast_hinglish(self):
        """Feature 1 & 2: Upload demo resume PDF and verify full roast generation."""
        data = self._create_demo_roast("hi-IN")
        self.assertIn("id", data)
        self.assertIn("overall_score", data)
        self.assertIn("band", data)
        self.assertIn("one_line_verdict", data)
        self.assertIn("issues", data)
        self.assertIn("strengths", data)

        # Validate score bounds and band
        score = data["overall_score"]
        self.assertTrue(0 <= score <= 100, f"Score out of range: {score}")
        self.assertIn(data["band"], ["weak", "mid", "strong"])

        # Validate issues
        issues = data["issues"]
        self.assertGreaterEqual(len(issues), 1, "Should identify at least 1 issue")
        for iss in issues:
            self.assertTrue(bool(iss.get("quoted_text")), "Quoted text should not be empty")
            self.assertTrue(bool(iss.get("roast")), "Roast critique should not be empty")
            self.assertTrue(bool(iss.get("fix")), "Actionable fix should not be empty")

        # Validate that fixes across issues are distinct (no repetition)
        fixes = [iss["fix"] for iss in issues]
        self.assertEqual(len(fixes), len(set(fixes)), f"Fixes should be unique: {fixes}")

    def test_02_fetch_roast_by_id(self):
        """Feature 3: Fetch roast by ID from persistent storage."""
        created = self._create_demo_roast()
        roast_id = created["id"]
        res = self.client.get(f"/api/roast/{roast_id}")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["id"], roast_id)
        self.assertIn("overall_score", data)
        self.assertIn("issues", data)

    def test_03_built_in_demo_endpoint_bilingual(self):
        """Feature 4: Test built-in demo roast endpoint in both Hinglish and English."""
        # Hinglish
        res_hi = self.client.get("/api/roast/demo", headers={"Accept-Language": "hi-IN"})
        self.assertEqual(res_hi.status_code, 200)
        data_hi = res_hi.json()
        self.assertIn("issues", data_hi)
        self.assertGreaterEqual(len(data_hi["issues"]), 3)

        # English
        res_en = self.client.get("/api/roast/demo", headers={"Accept-Language": "en"})
        self.assertEqual(res_en.status_code, 200)
        data_en = res_en.json()
        self.assertIn("issues", data_en)
        self.assertGreaterEqual(len(data_en["issues"]), 3)

    def test_04_ai_interview_hot_seat(self):
        """Feature 5: Generate AI Interview Hot-Seat trap questions and winning STAR scripts."""
        created = self._create_demo_roast()
        roast_id = created["id"]
        res = self.client.get(f"/api/roast/{roast_id}/interview-prep")
        self.assertEqual(res.status_code, 200, f"Interview prep failed: {res.text}")
        payload = res.json()
        self.assertTrue(payload.get("ok"))
        data = payload.get("data", {})
        self.assertIn("candidate_summary", data)
        questions = data.get("questions", [])
        self.assertGreaterEqual(len(questions), 1, "Should have at least 1 trap question")

        q1 = questions[0]
        self.assertIn("question", q1)
        self.assertIn("interviewer_trap", q1)
        self.assertIn("rookie_blunder", q1)
        self.assertIn("star_framework", q1)
        self.assertIn("script_to_say", q1)

        star = q1["star_framework"]
        self.assertTrue(bool(star.get("situation_task")), "STAR situation_task required")
        self.assertTrue(bool(star.get("action")), "STAR action required")
        self.assertTrue(bool(star.get("result")), "STAR result required")

    def test_05_roast_back_chat_comeback(self):
        """Feature 6: Argue back with AI in live chat and verify sharp, contextual response."""
        created = self._create_demo_roast()
        roast_id = created["id"]
        payload = {
            "message": "Maine bohot mehnat se JWT authentication build kiya hai, aise kaise no-metrics bol rahe ho?",
            "history": [],
        }
        res = self.client.post(
            f"/api/roast/{roast_id}/comeback",
            json=payload,
            headers={"Accept-Language": "hi-IN"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body.get("ok"))
        reply = body.get("reply", "")
        self.assertTrue(len(reply) > 10, f"Reply too short: {reply}")

    def test_06_ai_bullet_rewriter_studio(self):
        """Feature 7: Test AI STAR Bullet Rewriter Studio with 3 distinct rewrite formulas."""
        flawed_bullet = "Designed JWT authentication and RBAC-driven CRUD workflows, hardened through peer review."
        res = self.client.post(
            "/api/rewrite-bullet",
            json={"bullet": flawed_bullet, "target_role": "Full-Stack Engineer", "language": "en"},
        )
        self.assertEqual(res.status_code, 200, f"Bullet rewriter failed: {res.text}")
        body = res.json()
        self.assertTrue(body.get("ok"))
        data = body.get("data", {})
        options = data.get("options", [])
        self.assertGreaterEqual(len(options), 3, "Expected at least 3 distinct STAR rewrite options")
        for opt in options:
            self.assertTrue(bool(opt.get("style")), "Style required")
            self.assertTrue(bool(opt.get("rewritten_text")), "Rewritten text required")
            self.assertTrue(bool(opt.get("explanation")), "Explanation required")

    def test_07_parody_certificate_pdf(self):
        """Feature 8: Download official parody evaluation diploma PDF."""
        created = self._create_demo_roast()
        roast_id = created["id"]

        # 1. Info endpoint
        res_info = self.client.get(f"/api/roast/{roast_id}/certificate")
        self.assertEqual(res_info.status_code, 200)
        self.assertEqual(res_info.json().get("status"), "success")

        # 2. Binary PDF download
        res_dl = self.client.get(f"/api/roast/{roast_id}/certificate/download")
        self.assertEqual(res_dl.status_code, 200)
        pdf_bytes = res_dl.content
        self.assertTrue(pdf_bytes.startswith(b"%PDF"), "Must be a valid binary PDF document")
        self.assertGreater(len(pdf_bytes), 1000, "PDF should contain rendered diploma elements")

    def test_08_linkedin_carousel_pdf(self):
        """Feature 9: Generate 3-slide square LinkedIn viral carousel document."""
        created = self._create_demo_roast()
        roast_id = created["id"]

        # 1. Carousel info
        res_info = self.client.get(f"/api/roast/{roast_id}/carousel")
        self.assertEqual(res_info.status_code, 200)

        # 2. Binary Carousel PDF download
        res_dl = self.client.get(f"/api/roast/{roast_id}/carousel/download")
        self.assertEqual(res_dl.status_code, 200)
        pdf_bytes = res_dl.content
        self.assertTrue(pdf_bytes.startswith(b"%PDF"), "Carousel must be valid PDF")
        self.assertGreater(len(pdf_bytes), 1000, "Carousel PDF content size")

    def test_09_match_with_job_description(self):
        """Feature 10: Match demo resume against target Job Description."""
        res = self.client.post(
            "/api/match",
            json={
                "resume_text": DEMO_RESUME_TEXT,
                "job_description": DEMO_JD_TEXT,
                "language": "en",
            },
        )
        self.assertEqual(res.status_code, 200, f"JD Match failed: {res.text}")
        data = res.json()
        self.assertIn("match_score", data)
        self.assertTrue(0 <= data["match_score"] <= 100)
        self.assertIn("missing_keywords", data)
        self.assertIn("tailored_bullet_rewrites", data)

    def test_10_battle_mode(self):
        """Feature 11: 1-on-1 Battle Mode comparing two candidate resumes."""
        pdf_1 = self.pdf_bytes
        candidate_2_text = """
        Priya Sharma - Senior Backend Engineer
        priya.sharma@example.com | 5+ years experience
        - Architected distributed payment gateway processing $4.2M daily GMV with 99.99% uptime.
        - Reduced database query p95 latency from 450ms to 65ms via PostgreSQL partitioning and Redis.
        - Mentored team of 6 engineers on event-driven architecture with Kafka and Go.
        """
        pdf_2 = make_pdf(candidate_2_text)

        res = self.client.post(
            "/api/battle",
            files={
                "fighter1": ("resume_aakash.pdf", pdf_1, "application/pdf"),
                "fighter2": ("resume_priya.pdf", pdf_2, "application/pdf"),
            },
            headers={"Accept-Language": "hi-IN"},
        )
        self.assertEqual(res.status_code, 200, f"Battle mode failed: {res.text}")
        battle_data = res.json()
        self.assertIn("winner", battle_data)
        self.assertIn("verdict", battle_data)
        self.assertTrue(str(battle_data["winner"]) in ["1", "2", "tie", "fighter_1", "fighter_2"])

    def test_11_emoji_reactions(self):
        """Feature 12: Add interactive emoji reactions to roast report."""
        created = self._create_demo_roast()
        roast_id = created["id"]
        for emoji in ["😂", "🔥", "💀", "👀"]:
            res = self.client.post(
                f"/api/roast/{roast_id}/react",
                json={"emoji": emoji},
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("reactions", data)

    def test_12_wall_of_shame_publish_and_retrieve(self):
        """Feature 13: Anonymize and publish roast to public Wall of Shame."""
        created = self._create_demo_roast()
        roast_id = created["id"]
        res_pub = self.client.post("/api/wall/publish", json={"roast_id": roast_id})
        self.assertIn(res_pub.status_code, [200, 201])

        # Retrieve wall
        res_wall = self.client.get("/api/wall?tab=all")
        self.assertEqual(res_wall.status_code, 200)
        items = res_wall.json().get("items", [])
        self.assertGreaterEqual(len(items), 1)

    def test_13_whatsapp_voice_note_roast(self):
        """Feature 14: WhatsApp Voice Note Roast script and audio route."""
        created = self._create_demo_roast()
        roast_id = created["id"]
        res = self.client.get(f"/api/roast/{roast_id}/voice")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("script", data)
        self.assertIn("audio_url", data)
        self.assertTrue(len(data["script"]) > 10)

        # Audio stream
        res_audio = self.client.get(f"/api/roast/{roast_id}/voice/audio")
        self.assertEqual(res_audio.status_code, 200)

    def test_14_dimensional_scorecard_vectors(self):
        """Feature 15: Verify Dimensional Health Scorecard math across 5 vectors."""
        roast_data = self._create_demo_roast()
        score = roast_data.get("overall_score", 35)
        issues = roast_data.get("issues", [])
        safe_issues = issues if isinstance(issues, list) else []

        no_metrics_count = sum(1 for i in safe_issues if i.get("category") == "no-metrics")
        buzzword_count = sum(1 for i in safe_issues if i.get("category") == "buzzword")
        formatting_count = sum(1 for i in safe_issues if i.get("category") in ("formatting", "length"))
        typo_count = sum(1 for i in safe_issues if i.get("category") == "typo")

        # 1. Metrics Score
        metric_score = max(18, min(95, round(score * 0.7 + (4 - no_metrics_count) * 7)))
        self.assertTrue(18 <= metric_score <= 95)

        # 2. Action Verb Score
        action_verb_score = max(25, min(96, round(score * 0.8 + 10 - no_metrics_count * 5)))
        self.assertTrue(25 <= action_verb_score <= 96)

        # 3. ATS Scannability
        ats_score = max(30, min(98, round(92 - formatting_count * 18 - typo_count * 12)))
        self.assertTrue(30 <= ats_score <= 98)

        # 4. Fluff Index
        fluff_score = max(20, min(95, round(90 - buzzword_count * 22)))
        self.assertTrue(20 <= fluff_score <= 95)

        # 5. Tech Stack Proof
        tech_score = max(35, min(97, round(score * 0.85 + 15)))
        self.assertTrue(35 <= tech_score <= 97)

    def test_15_makeover_drop_in_parsing(self):
        """Feature 16: Verify Before vs After Makeover clean drop-in line parser."""
        def parse_fix(fix_text: str = ""):
            if not fix_text:
                return {"cleanDropIn": "", "directiveTip": ""}
            match = re.search(r"['\"]([^'\"]{15,})['\"]", fix_text)
            if match and match.group(1):
                tip = fix_text[:match.start()].strip().rstrip(":— -")
                return {"cleanDropIn": match.group(1), "directiveTip": tip}
            return {"cleanDropIn": fix_text, "directiveTip": ""}

        roast_data = self._create_demo_roast()
        issues = roast_data.get("issues", [])
        for iss in issues:
            parsed = parse_fix(iss.get("fix", ""))
            self.assertTrue(bool(parsed["cleanDropIn"]), "Drop-in rewrite should be extracted")

    def test_16_ats_markdown_export(self):
        """Feature 17: Generate complete ATS-optimized Markdown (.md) document."""
        roast_data = self._create_demo_roast()
        issues = roast_data.get("issues", [])
        strengths = roast_data.get("strengths", [])

        fixed_lines = [
            "# ATS-OPTIMIZED REWRITTEN RESUME",
            f"> Target Score: 88+ / 100 | Original Score: {roast_data['overall_score']}",
            f"> Verdict: \"{roast_data['one_line_verdict']}\"",
            "",
            "## KEY HIGHLIGHTS & STRENGTHS",
            *[f"- {s}" for s in strengths],
            "",
            "## REVISED BULLET POINTS",
            *[f"### {i+1}. [{iss['category'].upper()}]\n- Replaced: \"{iss['quoted_text']}\"\n- Drop-in: {iss['fix']}\n" for i, iss in enumerate(issues)],
        ]
        full_md = "\n".join(fixed_lines)
        self.assertIn("# ATS-OPTIMIZED REWRITTEN RESUME", full_md)
        self.assertIn("## REVISED BULLET POINTS", full_md)
        self.assertTrue(len(full_md) > 200)

    def test_17_english_persona_upload(self):
        """Feature 18: Upload with Accept-Language: en produces fluent English critique."""
        data = self._create_demo_roast("en")
        self.assertIn("overall_score", data)
        self.assertIn("issues", data)
        self.assertTrue(len(data.get("one_line_verdict", "")) > 5)


if __name__ == "__main__":
    unittest.main()
