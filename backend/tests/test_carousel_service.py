"""
Unit tests for LinkedIn Carousel PDF Generator
"""
import os
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.carousel_service import generate_linkedin_carousel_pdf


def test_generate_linkedin_carousel_pdf():
    dummy_data = {
        "score": 42,
        "band": "weak",
        "one_line_verdict": "A digital cry for help masquerading as a CV.",
        "issues": [
            {"quoted_text": "Responsible for daily operations", "roast": "Tells what you were assigned, not what you achieved."},
            {"quoted_text": "Hardworking and fast learner", "roast": "Standard cliché present on 90% of discarded resumes."},
        ],
        "strengths": ["Clean single-page format"],
    }
    pdf_path = generate_linkedin_carousel_pdf("test-carousel-123", dummy_data)
    assert os.path.exists(pdf_path)
    assert pdf_path.stat().st_size > 1000  # Multi-page PDF size is non-trivial


def test_download_carousel_demo_endpoint():
    client = TestClient(app)
    response = client.get("/api/carousel/demo/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "ResumeRoast-LinkedIn-Carousel" in response.headers.get("content-disposition", "")
    assert len(response.content) > 1000


def test_download_carousel_nonexistent_404():
    client = TestClient(app)
    response = client.get("/api/carousel/nonexistent-roast-id-404/download")
    assert response.status_code == 404
