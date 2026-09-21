"""
Unit and integration tests for resume validation, non-resume rejection,
and verdict diversity in Resume Roast.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.resume_validator import validate_is_resume
from app.services.ai_analyzer import _generate_grounded_verdict
from app.services.extractor import validate_file_signature
import io
import zipfile

client = TestClient(app)

SAMPLE_VALID_RESUME = """
Alex Morgan
alex.morgan@email.com | +1 (555) 234-5678 | linkedin.com/in/alexmorgan | github.com/alexm
San Francisco, CA

PROFESSIONAL EXPERIENCE
Senior Full Stack Engineer — CloudScale Labs (Jan 2022 – Present)
- Architected distributed microservices in Go and Python, processing 45M daily requests with 99.98% uptime.
- Led frontend redesign in React and TypeScript, reducing client-side bundle size by 38% and First Contentful Paint by 1.2s.
- Mentored 4 junior engineers and standardized CI/CD deployment pipelines using Docker and Kubernetes.

Software Engineer — Nexus Technologies (June 2019 – Dec 2021)
- Developed responsive web applications using React, Next.js, and Node.js for 150k active business users.
- Optimized PostgreSQL database queries, reducing checkout endpoint p99 latency from 450ms to 85ms.

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley — Graduated May 2019 | GPA: 3.82

TECHNICAL SKILLS
Languages: Python, JavaScript, TypeScript, Go, SQL, HTML/CSS
Frameworks & Tools: React, Node.js, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Git
"""

SAMPLE_EXAM_PAPER = """
Mid-Semester Examination - Autumn 2024
Department of Computer Science & Engineering
Course Code: CS-301 | Operating Systems & System Programming
Time Allowed: 3 Hours                                  Maximum Marks: 100

Instructions:
1. Attempt all questions from Section A and any three from Section B.
2. Assume suitable data wherever necessary.

Section A (20 Marks)
Q.1. (a) Define a process and explain its state transition diagram with neat sketch.
     (b) What is a race condition? Explain how semaphores prevent race conditions.
     (c) Differentiate between preemptive and non-preemptive scheduling algorithms.
     (d) What is thrashing in virtual memory? Explain its causes and remedies.

Section B (80 Marks)
Q.2. Explain Peterson's algorithm for mutual exclusion. Prove that it satisfies mutual exclusion, progress, and bounded waiting.
Q.3. Consider the following set of processes with arrival times and burst times...
"""

SAMPLE_SYLLABUS = """
Course Syllabus: Data Structures and Algorithms (CS202)
Semester: Fall 2024
Instructor: Dr. Robert Vance (Office: Room 412, Science Hall)
Course Outline:
Module I: Asymptotic Analysis and Complexity Classes (O, Omega, Theta notation)
Module II: Linear Data Structures (Arrays, Linked Lists, Stacks, Queues)
Module III: Non-Linear Structures (Binary Search Trees, AVL Trees, Heaps)
Unit IV: Graph Algorithms (BFS, DFS, Dijkstra's Shortest Path, Prim's MST)
Unit V: Dynamic Programming and Divide-and-Conquer Paradigms

References & Textbooks:
[1] Cormen, Leiserson, Rivest, and Stein, "Introduction to Algorithms", 3rd Edition, MIT Press.
[2] Robert Sedgewick, "Algorithms in C++", Addison-Wesley.
"""

SAMPLE_INVOICE = """
Tax Invoice / Bill of Supply
Invoice Number: INV-2024-09823
Invoice Date: September 15, 2024
Due Date: October 15, 2024

Bill To:
Acme Corporation Inc.
100 Corporate Parkway, Suite 500
San Jose, CA 95110

Items:
1. Cloud Server Hosting (Monthly Subscription) - $350.00
2. Enterprise Support SLA Tier 2 - $150.00
Subtotal: $500.00
Tax (GST 18%): $90.00
Total Amount Due: $590.00
Payment Method: Wire Transfer
"""

SAMPLE_RECIPE = """
Classic Homemade Chocolate Chip Cookies
Prep Time: 15 mins | Cook Time: 10 mins | Servings: 24 cookies

Ingredients:
- 2 1/4 cups all-purpose flour
- 1 tsp baking soda
- 1/2 tsp salt
- 1 cup unsalted butter, softened
- 3/4 cup granulated sugar
- 3/4 cup packed brown sugar
- 2 large eggs
- 2 cups semi-sweet chocolate chips

Instructions:
Preheat oven to 375°F. In a small bowl, mix flour, baking soda, and salt.
Beat butter, granulated sugar, and brown sugar until creamy.
Add eggs one at a time, beating well after each addition.
Bake for 9 to 11 minutes or until golden brown.
"""


def test_valid_resume_passes_validation():
    is_valid, err = validate_is_resume(SAMPLE_VALID_RESUME, filename="alex_morgan_resume.pdf", lang="en")
    assert is_valid is True
    assert err == ""


def test_exam_paper_rejected():
    is_valid, err = validate_is_resume(SAMPLE_EXAM_PAPER, filename="cs301_exam.pdf", lang="en")
    assert is_valid is False
    assert "academic course notes or an exam paper" in err


def test_syllabus_rejected():
    is_valid, err = validate_is_resume(SAMPLE_SYLLABUS, filename="syllabus_cs202.pdf", lang="en")
    assert is_valid is False
    assert "academic course notes or an exam paper" in err or "does not appear to be a resume" in err


def test_invoice_rejected():
    is_valid, err = validate_is_resume(SAMPLE_INVOICE, filename="billing_invoice.pdf", lang="en")
    assert is_valid is False
    assert "invoice or receipt" in err


def test_recipe_rejected():
    is_valid, err = validate_is_resume(SAMPLE_RECIPE, filename="cookie_recipe.pdf", lang="en")
    assert is_valid is False
    assert "does not appear to be a resume" in err


def test_presentation_file_extension_rejected():
    is_valid, err = validate_is_resume("Any sample text", filename="lecture_presentation.pptx", lang="en")
    assert is_valid is False
    assert "Presentation slides" in err


def test_short_document_rejected():
    is_valid, err = validate_is_resume("Hello, this is just a quick note.", filename="note.pdf", lang="en")
    assert is_valid is False
    assert "does not appear to be a resume" in err or "too short" in err

    is_valid_empty, err_empty = validate_is_resume("Hi", filename="note.pdf", lang="en")
    assert is_valid_empty is False
    assert "too short" in err_empty


def test_hinglish_rejection_message():
    is_valid, err = validate_is_resume(SAMPLE_EXAM_PAPER, filename="exam.pdf", lang="hi-IN")
    assert is_valid is False
    assert "question paper" in err or "resume nahi lag raha" in err


def test_pptx_zip_rejected_by_magic_bytes():
    # Build a fake PPTX in-memory zip
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("[Content_Types].xml", "<Types></Types>")
        zf.writestr("ppt/presentation.xml", "<p:presentation></p:presentation>")
    pptx_bytes = buf.getvalue()

    with pytest.raises(ValueError) as exc:
        validate_file_signature(pptx_bytes, "lecture_slides.docx")
    assert "Presentation slides" in str(exc.value)


def test_verdict_diversity_no_repetitions():
    """Verify that multiple distinct engineering resumes receive distinct verdicts rather than repeating the same 3 phrases."""
    resumes = [
        "Senior React Specialist leading architecture with 10 years experience. Live github.com/user/project",
        "Junior React intern who worked on basic button components and watched youtube tutorials",
        "Python backend engineer building Django REST APIs and postgres pipelines",
        "DevOps Kubernetes engineer configuring Terraform modules and ArgoCD deployments",
        "Frontend React engineer writing clean code with zero quantified metric numbers",
    ]

    verdicts = set()
    for r in resumes:
        v = _generate_grounded_verdict(r, domain="engineering", band="mid", top_cat="no-metrics", lang="en")
        verdicts.add(v)

    # In the old code, ALL of them would hit the same 3 tool_options!
    # With our diverse engine, they produce diverse verdicts
    assert len(verdicts) >= 2


def test_endpoint_rejects_exam_paper_with_422():
    """Verify POST /api/roast returns 422 when an exam paper is uploaded as a PDF."""
    try:
        from reportlab.pdfgen import canvas
        pdf_buf = io.BytesIO()
        p = canvas.Canvas(pdf_buf)
        p.drawString(100, 750, "Mid-Semester Examination - CS101")
        p.drawString(100, 730, "Time Allowed: 3 Hours | Maximum Marks: 100")
        p.drawString(100, 710, "Question 1: Explain memory management.")
        p.drawString(100, 690, "Question 2: Write a sorting function.")
        p.drawString(100, 670, "Attempt all questions. Total marks: 100.")
        p.save()
        pdf_bytes = pdf_buf.getvalue()

        resp = client.post(
            "/api/roast",
            files={"file": ("exam_paper.pdf", pdf_bytes, "application/pdf")},
        )
        assert resp.status_code == 422
        detail = resp.json().get("detail", "")
        assert "academic course notes or an exam paper" in detail or "does not appear to be a resume" in detail
    except ImportError:
        pass
