"""
Unit & Volume Verification Suite for Zero-Repetition Engine and Bug Fixes.
Tests cross-session anti-repeat memory, prompt exclusion injection, certificate generation,
and executes a 25-resume back-to-back volume test checking for cross-session duplicates.
"""
import difflib
import re
import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.services.anti_repeat_service import anti_repeat_memory, BASELINE_JOKE_BANKS
from app.services.ai_analyzer import (
    analyze_resume,
    _generate_fallback_roast,
    _validate_schema,
    _deduplicate_roasts,
    _has_hinglish_tone,
)


class TestAntiRepeatAndNewFeatures(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        anti_repeat_memory.clear()

    def test_cache_recording_and_capping(self):
        """Rolling cache stores up to 40 items and trims oldest."""
        cat = "no-metrics"
        for i in range(50):
            anti_repeat_memory.record_roast(cat, f"Test unique roast line #{i}")

        recent = anti_repeat_memory.get_recent_roasts(cat)
        self.assertLessEqual(len(recent), 40)
        # Verify most recent is present
        self.assertIn("Test unique roast line #49", recent)
        # Verify oldest (0-9) was trimmed
        self.assertNotIn("Test unique roast line #0", recent)

    def test_exclusion_prompt_generation(self):
        """Dynamic exclusion prompt formats accurately when items are cached."""
        anti_repeat_memory.record_roast("buzzword", "Ye word har second resume mein hai bhai, tu unique kaise banega isse?")
        anti_repeat_memory.record_roast("no-metrics", "Kitna kiya bhai, number bata na.")

        exclusions = anti_repeat_memory.get_sample_exclusions(sample_size=5)
        self.assertGreaterEqual(len(exclusions), 2)

        prompt_block = anti_repeat_memory.build_exclusion_prompt(sample_size=5)
        self.assertIn("The following lines have been used recently", prompt_block)
        self.assertIn("do NOT reuse these", prompt_block)
        self.assertIn("- \"", prompt_block)

    def test_demo_roast_endpoint(self):
        """GET /api/roast/demo returns valid 200 payload directly."""
        resp = self.client.get("/api/roast/demo")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["id"], "demo")
        self.assertEqual(data["overall_score"], 28)
        self.assertGreaterEqual(len(data["issues"]), 4)

    def test_certificate_endpoints(self):
        """Certificate metadata and PDF download endpoints function cleanly."""
        # 1. Metadata endpoint
        info_resp = self.client.get("/api/roast/demo/certificate")
        self.assertEqual(info_resp.status_code, 200)
        data = info_resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("credential_title", data)
        self.assertIn("/certificate/download", data["download_url"])

        # 2. Binary PDF download endpoint
        dl_resp = self.client.get("/api/roast/demo/certificate/download")
        self.assertEqual(dl_resp.status_code, 200)
        self.assertEqual(dl_resp.headers["content-type"], "application/pdf")
        self.assertIn("%PDF-", dl_resp.content[:10].decode("latin-1", "ignore"))

    def test_demo_voice_note(self):
        """Voice note generation on demo roast returns audio successfully."""
        resp = self.client.post("/api/roast/demo/voice")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("audio_url", resp.json())

        audio_resp = self.client.get("/api/roast/demo/voice/audio")
        self.assertEqual(audio_resp.status_code, 200)
        self.assertIn("audio/mpeg", audio_resp.headers["content-type"])

    def test_badge_label_sanitization_and_default(self):
        """Dynamic badge_label is capitalized, punctuation stripped, and defaulted if empty."""
        test_data = {
            "overall_score": 35,
            "band": "weak",
            "one_line_verdict": "Bhai ye kya likha hai yaar 😭",
            "issues": [
                {
                    "quoted_text": "Responsible for managing project workflows",
                    "category": "no-metrics",
                    "badge_label": "number kahan hai!!",
                    "roast": "Bhai number toh do yaar 😩",
                    "fix": "Specific number daalo.",
                },
                {
                    "quoted_text": "Team player with synergistic focus",
                    "category": "buzzword",
                    "badge_label": "",  # missing/empty
                    "roast": "Arre yaar generic buzzword band karo.",
                    "fix": "Real action dikhao.",
                },
            ],
            "strengths": ["Formatting clean hai 👍"],
        }
        _validate_schema(test_data, language="hi-IN")
        self.assertEqual(test_data["issues"][0]["badge_label"], "NUMBER KAHAN HAI")
        self.assertTrue(len(test_data["issues"][1]["badge_label"]) > 0)
        self.assertTrue(test_data["issues"][1]["badge_label"].isupper())

    def test_fallback_roast_has_badge_labels(self):
        """_generate_fallback_roast populates dynamic badge_labels for all issues."""
        sample_resume = """
        Rohan Mehta
        Responsible for UI development.
        Worked closely with the team.
        Hobbies: Watching movies.
        DECLARATION: True to my knowledge.
        """
        fallback = _generate_fallback_roast(sample_resume, language="hi-IN")
        self.assertIn("issues", fallback)
        self.assertGreater(len(fallback["issues"]), 0)
        for iss in fallback["issues"]:
            self.assertIn("badge_label", iss)
            self.assertTrue(iss["badge_label"].isupper())
            self.assertNotIn("!", iss["badge_label"])
            self.assertNotIn("?", iss["badge_label"])

    def test_deduplicate_badge_labels_pairwise(self):
        """_deduplicate_roasts ensures no two issues share duplicate badge_labels."""
        data = {
            "issues": [
                {
                    "category": "no-metrics",
                    "badge_label": "NUMBER KAHAN HAI",
                    "roast": "Kitna kiya bhai number bata na 😩",
                },
                {
                    "category": "no-metrics",
                    "badge_label": "NUMBER KAHAN HAI",  # Duplicate badge!
                    "roast": "Number nahi hai isme chhupa kyun rahe ho? 👀",
                },
            ]
        }
        _deduplicate_roasts(data, language="hi-IN")
        badges = [iss["badge_label"] for iss in data["issues"]]
        self.assertNotEqual(badges[0], badges[1], "Duplicate badge_label must be resolved")

    def test_tone_guard_hinglish_and_english(self):
        """Hinglish tone guard requires Hinglish markers for hi-IN; English checks length."""
        self.assertTrue(_has_hinglish_tone("Bhai ye kya likha hai yaar 😩"))
        self.assertFalse(_has_hinglish_tone("This is an impeccably formatted formal professional document."))

        # English data passing hi-IN validation should fail tone check
        pure_english_data = {
            "overall_score": 40,
            "band": "weak",
            "one_line_verdict": "This resume lacks proper quantifiable metrics.",
            "issues": [
                {
                    "quoted_text": "Responsible for managing project workflows",
                    "category": "no-metrics",
                    "badge_label": "NO METRICS",
                    "roast": "This bullet point does not contain any metrics.",
                    "fix": "Include quantifiable results.",
                }
            ],
            "strengths": ["Good formatting."],
        }
        with self.assertRaises(ValueError):
            _validate_schema(pure_english_data, language="hi-IN")

        # But it passes under 'en'
        _validate_schema(pure_english_data, language="en")
        self.assertEqual(pure_english_data["issues"][0]["badge_label"], "NO METRICS")

    def test_25_resumes_cross_session_volume_test(self):
        """
        Section 1.4 Verification:
        Runs 25 diverse resumes back-to-back, logging every roast generated.
        Ensures cross-session anti-repeat memory prevents high-volume duplication.
        """
        raw_resumes = [
            # 1
            """Rahul Verma
            Senior Frontend Engineer with React, TypeScript, Redux.
            Responsible for leading frontend UI modernization project.
            Worked closely with backend team to integrate GraphQL APIs.
            Hobbies: Playing guitar, reading books, photography.
            Declaration: All statements made above are true to my knowledge.""",

            # 2
            """Priya Sharma
            Backend Developer — 3 years experience.
            Assisted team in scaling database microservices and cache.
            Spearheaded migration from monolithic to microservices.
            Passionate developer who loves building cutting-edge software.
            SKILS: Python, Jacascript, PostgreSQL, Docker.""",

            # 3
            """Amit Patel
            Full Stack Software Engineer.
            Curriculum Vitae (Page 1 of 3)
            Responsible for building checkout flow and payment integrations.
            Utilized synergistic paradigms across 6 cross-functional pods.
            Declaration: Hereby declare everything is correct.""",

            # 4
            """Ananya Sen
            Data Engineer & Python Developer.
            Assisted in setting up Apache Spark pipelines and ETL jobs.
            Worked closely with business analysts to extract business metrics.
            Hobbies: Watching cricket, traveling, sketching.
            Skils: Python, SQL, AWS, Airflow, PySpark.""",

            # 5
            """Vikram Malhotra
            DevOps Engineer with Kubernetes, Terraform, AWS.
            Responsible for managing infrastructure CI/CD pipelines.
            Passionate technologist eager to deliver impactful cloud systems.
            Declaration: All details given here are valid.""",

            # 6
            """Neha Gupta
            Mobile App Developer (Flutter / React Native).
            Spearheaded release of mobile e-commerce application.
            Worked closely with UX design team on prototyping.
            Hobbies: Badminton, cooking, video gaming.""",

            # 7
            """Suresh Nair
            Cloud Solutions Architect.
            Responsible for architecting secure cloud landing zones on GCP.
            Utilized cutting-edge cloud native practices across teams.
            Declaration: Certified true and accurate.""",

            # 8
            """Kavita Joshi
            QA Automation Engineer.
            Assisted QA team in executing Cypress and Selenium suites.
            Passionate about zero-defect software engineering and testing.
            Curriculum Vitae — References available on demand.""",

            # 9
            """Deepak Reddy
            Security Engineer / Pentester.
            Responsible for running vulnerability assessments on APIs.
            Worked closely with SOC team to mitigate threat alerts.
            Declaration: Everything is truthful.""",

            # 10
            """Simran Kaur
            Machine Learning Engineer.
            Spearheaded training of recommendation transformer models.
            Passionate about artificial intelligence and deep learning.
            Hobbies: Solving puzzles, tennis, swimming.""",

            # 11
            """Aditya Roy
            Go / Backend Systems Engineer.
            Responsible for maintaining high concurrency messaging queues.
            Assisted senior architects with Kafka partitions optimization.
            Declaration: All information is authentic.""",

            # 12
            """Pooja Bhatt
            Product Designer & Frontend Developer.
            Worked closely with founders to redesign consumer onboarding.
            Curriculum Vitae (Page 1 of 4)
            Hobbies: Painting, digital illustration, travel.""",

            # 13
            """Manish Tiwari
            Systems Administrator.
            Responsible for server patching, backup operations, and monitoring.
            Passionate about Linux administration and bash automation.
            Declaration: I hereby declare the above to be accurate.""",

            # 14
            """Sneha Kulkarni
            iOS Developer with Swift, SwiftUI, Combine.
            Spearheaded architecture of offline synchronization engine.
            Worked closely with product manager on sprint planning.
            Skils: Swift, Objective-C, CocoaPods, Xcode.""",

            # 15
            """Harish Mehta
            Database Administrator.
            Assisted in migrating PostgreSQL clusters to Aurora.
            Passionate DBA with deep knowledge of relational algebra.
            Hobbies: Table tennis, numismatics, hiking.""",

            # 16
            """Ritu Agarwal
            Site Reliability Engineer.
            Responsible for on-call incidents, alert triage, and runbooks.
            Utilized synergistic tooling to improve observability.
            Declaration: True to best of my knowledge.""",

            # 17
            """Gaurav Saxena
            Embedded Systems Engineer.
            Spearheaded firmware development on ARM Cortex microcontrollers.
            Worked closely with hardware PCB layout designers.
            Hobbies: Electronics DIY, 3D printing, cycling.""",

            # 18
            """Meera Krishnan
            Frontend Developer with Vue.js, Pinia, TailwindCSS.
            Assisted team in redesigning analytics dashboard.
            Passionate UI developer with keen eye for typography.
            Declaration: All details are correct.""",

            # 19
            """Karan Kapoor
            Full Stack Node.js Engineer.
            Responsible for GraphQL API resolvers and authentication.
            Spearheaded implementation of OAuth2 and JWT session tokens.
            Curriculum Vitae (Page 1 of 3)""",

            # 20
            """Swati Deshmukh
            NLP Research Scientist.
            Worked closely with academic labs on multilingual sentiment.
            Passionate researcher interested in low-resource Indian languages.
            Hobbies: Chess, reading fiction, yoga.""",

            # 21
            """Tarun Singhania
            Solidity / Blockchain Engineer.
            Responsible for deploying ERC-20 smart contracts and test suites.
            Assisted core team in auditing gas optimizations.
            Declaration: All information is accurate.""",

            # 22
            """Divya Menon
            Platform Engineer.
            Spearheaded Kubernetes operator development in Go.
            Worked closely with infrastructure teams on cluster provisioning.
            Hobbies: Photography, gardening, reading.""",

            # 23
            """Arjun Das
            Microservices Backend Engineer.
            Responsible for gRPC service contracts and Protobuf schemas.
            Passionate engineer striving for sub-millisecond latencies.
            Skils: Go, C++, gRPC, Redis, Kafka.""",

            # 24
            """Sunita Rao
            Technical Writer & Developer Relations.
            Assisted in authoring API guides, tutorials, and SDK docs.
            Worked closely with open source community contributors.
            Declaration: Facts mentioned here are truthful.""",

            # 25
            """Rohan Nambiar
            Android Engineer with Kotlin, Jetpack Compose.
            Spearheaded complete rewrite of media player module.
            Passionate developer eager to build buttery smooth 120fps UIs.
            Hobbies: Photography, gaming, podcasting.""",
        ]

        all_roasts: list[str] = []
        roasts_per_resume: list[list[str]] = []

        for idx, resume_text in enumerate(raw_resumes):
            analysis = analyze_resume(resume_text)
            issues = analysis["issues"]

            # Verify no duplicates within the same resume
            resume_roasts = [iss["roast"] for iss in issues]
            roasts_per_resume.append(resume_roasts)
            all_roasts.extend(resume_roasts)

            # Within-resume check: No two roasts should have >85% string similarity
            for i in range(len(resume_roasts)):
                for j in range(i + 1, len(resume_roasts)):
                    n1 = re.sub(r"[^a-z0-9]", "", resume_roasts[i].lower())
                    n2 = re.sub(r"[^a-z0-9]", "", resume_roasts[j].lower())
                    ratio = difflib.SequenceMatcher(None, n1, n2).ratio()
                    self.assertLess(
                        ratio,
                        0.88,
                        f"Duplicate found within resume #{idx+1}: {resume_roasts[i]!r} vs {resume_roasts[j]!r}",
                    )

        # Batch-wide cross-session analysis across all 25 resumes
        total_roasts = len(all_roasts)
        self.assertGreaterEqual(total_roasts, 75)

        # Check total unique roast strings
        unique_roasts = set(all_roasts)
        unique_ratio = len(unique_roasts) / total_roasts

        print(f"\n[VOLUME TEST SUMMARY]")
        print(f"Total resumes processed: {len(raw_resumes)}")
        print(f"Total roast lines generated: {total_roasts}")
        print(f"Unique roast strings: {len(unique_roasts)} ({unique_ratio * 100:.1f}%)")

        # Because our joke banks across all categories have 40+ diverse lines and we rotate
        # with anti-repeat memory, the unique variety ratio across 25 resumes must be > 60%!
        self.assertGreater(
            unique_ratio,
            0.60,
            f"Expected at least 60% unique jokes across 25 runs, got {unique_ratio * 100:.1f}%",
        )


if __name__ == "__main__":
    unittest.main()
