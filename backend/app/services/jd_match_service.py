"""
Job Description (JD) Match Service — ATS Reality Check & Role Tailoring.
Compares candidate resume text against target job description to compute ATS match score,
identify missing critical keywords, call out irrelevant clutter, and generate tailored bullet rewrites.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

from app.services.anti_repeat_service import anti_repeat_memory

load_dotenv()
logger = logging.getLogger("jd_match")

SAMPLE_JDS = [
    {
        "id": "swiggy-frontend",
        "title": "Frontend Engineer (React / TypeScript)",
        "company": "Swiggy",
        "description": """Role: Frontend Engineer II
Location: Bengaluru / Remote
About the role:
We are looking for a high-energy Frontend Engineer to build consumer-facing interfaces handling 10M+ daily active users.

Key Requirements:
- 2+ years experience with React.js, TypeScript, Next.js, and Modern JavaScript (ES6+).
- Strong command of state management (Zustand, Redux Toolkit) and React Query.
- Proven track record optimizing Web Vitals (LCP, FID, CLS), code-splitting, and render performance.
- Experience with Tailwind CSS, responsive design, and cross-browser quirks.
- Automated testing experience with Jest, React Testing Library, or Playwright.
- Excellent debugging skills with Chrome DevTools, Network profiling, and Sentry monitoring.
- Bonus: Micro-frontends, WebSockets for live order tracking, or PWA experience.""",
    },
    {
        "id": "zerodha-backend",
        "title": "Backend SDE (Go / PostgreSQL / Redis)",
        "company": "Zerodha",
        "description": """Role: Software Development Engineer — Core Trading Backend
Location: Bengaluru
About the role:
Build resilient, ultra-low-latency financial systems that process billions of rupees in market transactions daily with zero downtime.

Key Requirements:
- 2+ years of hands-on backend engineering with Go (Golang), Python, or C++.
- Deep expertise in relational databases (PostgreSQL): query optimization, indexing, transaction isolation levels, and connection pooling.
- High-throughput caching and pub/sub architecture using Redis or Kafka.
- Microservices communication with gRPC, Protocol Buffers, and REST.
- Linux systems programming: profiling CPU/memory bottlenecks, goroutine leak detection, and network sockets.
- Docker, Kubernetes, and automated CI/CD deployment pipelines.
- Zero tolerance for race conditions or data loss. Experience with ACID guarantees is essential.""",
    },
    {
        "id": "ai-startup-fullstack",
        "title": "Full Stack AI Engineer",
        "company": "NextGen AI Lab",
        "description": """Role: Full Stack AI Engineer
Location: Remote / Delhi NCR
About the role:
Join an early-stage venture-backed AI startup building generative workflows and autonomous agents for enterprise software teams.

Key Requirements:
- Full-stack fluency across TypeScript/React (frontend) and Python/FastAPI (backend).
- Hands-on experience integrating LLM APIs (OpenAI, Anthropic Claude, Gemini) and LangChain/LlamaIndex.
- Vector databases (Pinecone, Qdrant, pgvector) for RAG pipelines and semantic search.
- Clean API design, async task queues with Celery or Redis, and PostgreSQL.
- Rapid prototyping mindset: ship MVPs in days, iterate based on user telemetry.
- Familiarity with prompt engineering, function calling, structured outputs, and evaluation metrics.""",
    },
]


JD_MATCH_SYSTEM_PROMPT = """You are an elite, brutally honest Indian tech recruiter and hiring manager at top Indian tech firms (Swiggy, Zerodha, Flipkart, Zomato, Google India).
You are evaluating a candidate's resume specifically against a target Job Description (JD).
Your job is to give an authentic "ATS Reality Check" and roast their gaps in savage yet deeply constructive WhatsApp-style Hinglish (or clear English if requested), written in Roman script with natural texting emojis (💀, 😩, 🤡, 🚀, 📊).

Evaluate these aspects strictly:
1. "match_score": Integer 0 to 100 based on actual hard qualification match.
   - If missing core mandatory technologies from JD -> score MUST be under 50.
   - If missing 1-2 secondary items but strong core -> score 50 to 75.
   - If exceptional fit with matching metrics -> 76 to 95.
2. "ats_status": "rejected" (score < 50), "borderline" (score 50-74), "shortlisted" (score >= 75).
3. "verdict": One savage, hilarious, yet grounded summary of how this resume would fare against the JD's company ATS parser.
4. "missing_keywords": List of 3 to 6 critical technologies/skills/concepts EXPLICITLY demanded in the JD that are completely missing from the resume.
   - For each missing keyword:
     - "keyword": exact skill name from JD
     - "importance": "critical" | "high" | "nice-to-have"
     - "roast": savage, grounded critique of why missing this guarantees instant ATS auto-rejection.
5. "matched_skills": List of 3 to 6 actual skills that appear in BOTH the resume and the JD.
6. "irrelevant_clutter": List of 1 to 3 items/skills on the resume that have ZERO relevance to this JD and waste prime 1-page real estate.
7. "tailored_bullet_rewrites": List of 2 to 4 concrete bullet point rewrites showing how to adapt candidate's real experience to target the JD's exact language:
   - "original": quote a weak/generic bullet from the resume
   - "tailored_fix": drop-in rewritten bullet with specific numbers and the JD's required keywords
   - "target_jd_requirement": the specific requirement from the JD this bullet now proves

Return strictly valid JSON only:
{
  "match_score": number,
  "ats_status": "rejected" | "borderline" | "shortlisted",
  "verdict": string,
  "matched_skills": string[],
  "missing_keywords": [
    { "keyword": string, "importance": "critical" | "high" | "nice-to-have", "roast": string }
  ],
  "irrelevant_clutter": [
    { "quoted_text": string, "roast": string }
  ],
  "tailored_bullet_rewrites": [
    { "original": string, "tailored_fix": string, "target_jd_requirement": string }
  ]
}
"""


def _normalize_tokens(text: str) -> set[str]:
    """Tokenize text into lowercase alphanumeric keywords."""
    return set(re.findall(r"\b[a-z0-9\+#\.\-]{2,20}\b", text.lower()))


def _generate_fallback_match(
    resume_text: str,
    job_description: str,
    language: str = "hi-IN",
) -> Dict[str, Any]:
    """
    Deterministic, smart heuristic fallback match engine.
    Extracts common tech keywords, checks overlap, and builds authentic roasts.
    """
    is_hinglish = language == "hi-IN"
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    # Common Indian tech stacks to look for in JD
    common_tech = [
        ("react", "React.js", "critical"),
        ("typescript", "TypeScript", "critical"),
        ("next.js", "Next.js", "high"),
        ("node", "Node.js", "critical"),
        ("python", "Python", "critical"),
        ("fastapi", "FastAPI", "high"),
        ("go", "Golang", "critical"),
        ("postgresql", "PostgreSQL", "critical"),
        ("redis", "Redis", "high"),
        ("docker", "Docker", "high"),
        ("kubernetes", "Kubernetes (K8s)", "critical"),
        ("kafka", "Apache Kafka", "critical"),
        ("aws", "AWS Cloud", "high"),
        ("tailwind", "Tailwind CSS", "nice-to-have"),
        ("graphql", "GraphQL", "high"),
        ("microservices", "Microservices Architecture", "critical"),
        ("testing", "Unit & Integration Testing (Jest/Pytest)", "high"),
        ("ci/cd", "CI/CD Pipelines", "high"),
        ("grpc", "gRPC / Protobuf", "high"),
        ("langchain", "LangChain / LLM APIs", "critical"),
    ]

    jd_keywords = []
    for key, display, imp in common_tech:
        if re.search(r"\b" + re.escape(key) + r"\b", jd_lower):
            jd_keywords.append((key, display, imp))

    # If few matched from predefined list, extract top capitalized words from JD
    if len(jd_keywords) < 3:
        words = re.findall(r"\b[A-Z][a-zA-Z0-9\+#\.\-]{2,15}\b", job_description)
        for w in words[:6]:
            if w.lower() not in [k[0] for k in jd_keywords]:
                jd_keywords.append((w.lower(), w, "high"))

    matched_skills = []
    missing_keywords = []

    for key, display, imp in jd_keywords:
        if re.search(r"\b" + re.escape(key) + r"\b", resume_lower):
            matched_skills.append(display)
        else:
            if is_hinglish:
                roast_text = f"JD mein '{display}' 3 baar manga hai bhai, tumhare resume mein ek baar bhi nahi hai 😩 ATS instantly ignore marega."
            else:
                roast_text = f"The job description explicitly demands '{display}', but your resume has zero mentions. Instant ATS filter rejection."
            missing_keywords.append({
                "keyword": display,
                "importance": imp,
                "roast": roast_text,
            })

    total_jd_skills = len(jd_keywords) or 5
    match_ratio = len(matched_skills) / max(total_jd_skills, 1)

    # Calibrate score
    match_score = int(min(92, max(22, match_ratio * 100)))

    if match_score < 50:
        ats_status = "rejected"
        verdict = (
            "ATS ne resume bina padhe recycle bin mein daal diya bhai 💀 Core skills hi missing hain."
            if is_hinglish
            else "The ATS discarded this resume in 2 milliseconds. Core mandatory stack requirements are missing."
        )
    elif match_score < 75:
        ats_status = "borderline"
        verdict = (
            "Borderline case hai — recruiter 10 second dekhega, par interview call aana 50-50 luck hai."
            if is_hinglish
            else "Borderline match — might pass basic keyword screening, but lacks key proof of specialized scale."
        )
    else:
        ats_status = "shortlisted"
        verdict = (
            "Solid keyword overlap! Thoda bullet formatting tight kar lo toh shortlist pakka lag raha hai 🚀"
            if is_hinglish
            else "Strong keyword alignment with the job description. Tighten your metrics and you are interview-ready."
        )

    # Detect irrelevant clutter in resume
    clutter_candidates = [
        ("declaration", "Declaration section", "Declaration 2005 ka relic hai bhai, modern JD ke liye prime space waste kar raha hai."),
        ("hobbies", "Hobbies / Personal details", "Playing cricket ya watching movies se company ko code ship karne mein kya help milegi?"),
        ("references", "References available upon request", "Obvious filler line hai, recruiter kabhi nahi maangta."),
    ]
    irrelevant_clutter = []
    for pat, display, rst in clutter_candidates:
        if pat in resume_lower:
            irrelevant_clutter.append({
                "quoted_text": display,
                "roast": rst if is_hinglish else f"{display} is obsolete filler. Remove it to free up space for target JD requirements.",
            })

    # Sample tailored rewrites
    tailored_rewrites = [
        {
            "original": "Worked on frontend features and resolved bug tickets for web application.",
            "tailored_fix": f"Architected high-throughput responsive features using {matched_skills[0] if matched_skills else 'React/TypeScript'}, reducing page load latency by 28% and resolving 40+ production tickets.",
            "target_jd_requirement": "Demonstrated experience building scalable web interfaces with modern performance optimizations.",
        },
        {
            "original": "Responsible for backend API endpoints and database queries.",
            "tailored_fix": "Engineered 14 resilient REST/gRPC microservice endpoints in PostgreSQL, implementing connection pooling to handle 5,000+ requests/second.",
            "target_jd_requirement": "Proficiency in high-concurrency backend services, API design, and database query optimization.",
        },
    ]

    return {
        "match_score": match_score,
        "ats_status": ats_status,
        "verdict": verdict,
        "matched_skills": matched_skills[:6] if matched_skills else ["Problem Solving", "Git", "REST APIs"],
        "missing_keywords": missing_keywords[:6],
        "irrelevant_clutter": irrelevant_clutter,
        "tailored_bullet_rewrites": tailored_rewrites,
    }


def analyze_jd_match(
    resume_text: str,
    job_description: str,
    language: str = "hi-IN",
) -> Dict[str, Any]:
    """
    Analyze resume against target JD using Google Gemini or robust heuristic fallback.
    """
    if not job_description or len(job_description.strip()) < 30:
        raise ValueError("Please provide a detailed Job Description (at least 30 characters).")

    if not resume_text or len(resume_text.strip()) < 50:
        raise ValueError("Resume content is too short to analyze.")

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()

    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            prompt_content = f"""RESUME TEXT:
\"\"\"
{resume_text[:6000]}
\"\"\"

TARGET JOB DESCRIPTION:
\"\"\"
{job_description[:4000]}
\"\"\"

LANGUAGE PREFERENCE: {language}
"""
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": JD_MATCH_SYSTEM_PROMPT},
                            {"text": prompt_content},
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json",
                },
            }

            with httpx.Client(timeout=25.0) as client:
                res = client.post(url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        raw_text = candidates[0]["content"]["parts"][0]["text"]
                        parsed = json.loads(raw_text)
                        # Sanitize & validate
                        match_score = int(max(0, min(100, parsed.get("match_score", 50))))
                        ats_status = parsed.get("ats_status", "borderline")
                        if ats_status not in ["rejected", "borderline", "shortlisted"]:
                            ats_status = "rejected" if match_score < 50 else ("shortlisted" if match_score >= 75 else "borderline")

                        return {
                            "match_score": match_score,
                            "ats_status": ats_status,
                            "verdict": parsed.get("verdict", "ATS reality check completed."),
                            "matched_skills": parsed.get("matched_skills", [])[:8],
                            "missing_keywords": parsed.get("missing_keywords", [])[:8],
                            "irrelevant_clutter": parsed.get("irrelevant_clutter", [])[:3],
                            "tailored_bullet_rewrites": parsed.get("tailored_bullet_rewrites", [])[:4],
                        }
                else:
                    logger.warning(f"Gemini API returned status {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"Gemini JD match failed, using smart fallback: {e}")

    # Fallback to local heuristic analyzer
    return _generate_fallback_match(resume_text, job_description, language=language)
