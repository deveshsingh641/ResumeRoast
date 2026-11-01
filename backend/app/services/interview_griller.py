"""
AI Interview Hot-Seat & Griller Service
Predicts the brutal trap questions interviewers will ask based on the candidate's
specific resume weaknesses and provides high-impact STAR answer survival scripts.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import httpx

logger = logging.getLogger(__name__)


class StarFramework(BaseModel):
    situation_task: str = Field(description="Context and specific challenge")
    action: str = Field(description="Concrete individual technical actions taken")
    result: str = Field(description="Measurable business or technical outcome")


class InterviewQuestion(BaseModel):
    id: int
    flaw_reference: str
    category: str
    difficulty: str  # "Crucial", "Tough", "Brutal"
    question: str
    interviewer_trap: str
    rookie_blunder: str
    star_framework: StarFramework
    script_to_say: str


class InterviewPrepResult(BaseModel):
    roast_id: str
    candidate_summary: str
    questions: List[InterviewQuestion]
    source: str = "ai"  # "ai" or "smart_engine"


def _generate_smart_fallback_questions(
    roast_data: Dict[str, Any],
    roast_id: str = "demo",
    language: str = "en",
) -> InterviewPrepResult:
    """Generate high-impact, realistic interview trap questions derived from actual issues."""
    issues = roast_data.get("issues", [])
    score = roast_data.get("overall_score", 50)
    is_hinglish = language == "hi-IN"

    questions: List[InterviewQuestion] = []
    
    # 1. Question from First Flaw / Metrics
    flaw_1 = issues[0] if len(issues) > 0 else {}
    quote_1 = flaw_1.get("quoted_text", "Responsible for developing applications")
    
    questions.append(
        InterviewQuestion(
            id=1,
            flaw_reference=quote_1,
            category="Metrics & Impact Probe",
            difficulty="Brutal",
            question=(
                f"You wrote '{quote_1}' on your resume. That sounds vague. "
                "Can you walk me through the exact numbers: what was the scale, the benchmark before you joined, "
                "and what measurable KPI moved because of your personal code?"
            ),
            interviewer_trap=(
                "Interviewers use this to filter out candidates who exaggerate. "
                "They want to see if you can quantify engineering value or if you just rode on the team's coattails."
            ),
            rookie_blunder=(
                "Saying 'It was a large team project so I don't have the exact metrics' — this immediately raises suspicion."
                if not is_hinglish
                else "Ye bolna ki 'Team ne banaya tha mujhe numbers ka exact idea nahi' — interviewer turant disqualify kar deta hai."
            ),
            star_framework=StarFramework(
                situation_task="Our service was struggling with performance bottlenecks and lack of visibility under peak loads.",
                action="I instrumented structured APM logging, identified the 3 slowest database queries, and implemented Redis query caching.",
                result="Decreased p95 API response times by 48% and prevented recurring timeout spikes during flash events.",
            ),
            script_to_say=(
                "When I took ownership of that module, response times were hovering around 850ms during peak hours. "
                "I profiled the execution graph, decoupled blocking synchronous I/O into background celery workers, "
                "and reduced overall latency to under 120ms while saving roughly 20% in server compute costs."
            ),
        )
    )

    # 2. Question from Second Flaw / Buzzwords or Architecture
    flaw_2 = issues[1] if len(issues) > 1 else (issues[0] if issues else {})
    quote_2 = flaw_2.get("quoted_text", "Collaborated with cross-functional teams")
    
    questions.append(
        InterviewQuestion(
            id=2,
            flaw_reference=quote_2,
            category="Ownership & Conflict Resolution",
            difficulty="Tough",
            question=(
                f"Regarding your point: '{quote_2}' — tell me about a time you had a technical disagreement "
                "with a senior engineer or product manager on this deliverable. How did you resolve it?"
            ),
            interviewer_trap=(
                "They are testing your emotional intelligence, technical courage, and whether you blindly accept bad specs "
                "or use data to build engineering consensus."
            ),
            rookie_blunder=(
                "Saying 'We never had disagreements, everyone agreed' — proves inexperience or passivity."
            ),
            star_framework=StarFramework(
                situation_task="Product requested adding a complex real-time search feature 3 days before a major release.",
                action="I ran benchmark load tests proving real-time indexing would crash our primary DB; presented a phased rollout with debounce caching as a compromise.",
                result="Shipped the core release on schedule with zero downtime, and rolled out optimized search in the subsequent sprint.",
            ),
            script_to_say=(
                "We had a situation where product wanted a synchronous audit log on every mutation. "
                "I demonstrated via load testing that it would double transaction times, so I proposed writing audit events asynchronously "
                "to an event queue. The team adopted that architecture, preserving both strict audit compliance and sub-100ms API speeds."
            ),
        )
    )

    # 3. Question on Tech Stack Depth / Architectural Trade-offs
    questions.append(
        InterviewQuestion(
            id=3,
            flaw_reference="Technical stack selections and claims",
            category="System Design & Trade-offs",
            difficulty="Crucial",
            question=(
                "What is the single biggest architectural limitation of the stack you chose for your primary project, "
                "and if you were given another month with 10x traffic, what would you refactor first?"
            ),
            interviewer_trap=(
                "Differentiates junior coders from senior engineers. Senior engineers know every framework has trade-offs and failure modes."
            ),
            rookie_blunder=(
                "Saying 'Our architecture was perfect with no limitations' — signals an inability to think critically about scale."
            ),
            star_framework=StarFramework(
                situation_task="Our monolithic relational database became the primary contention point as concurrent connections surged.",
                action="I evaluated connection pooling, read replicas, and query optimization before deciding which pieces to shard.",
                result="Maintained 99.95% uptime and established a blueprint to scale from 10k to 100k daily active users.",
            ),
            script_to_say=(
                "The biggest limitation was our reliance on synchronous relational DB joins for historical reporting. "
                "At 10x traffic, connection pool exhaustion would be the first point of failure. "
                "If refactoring, I would implement CDC (Change Data Capture) into a read-optimized columnar store like ClickHouse or an elastic search cluster."
            ),
        )
    )

    summary = (
        f"Based on your resume score of {score}/100 and detected weaknesses, "
        "interviewers will aggressively probe your quantification, individual ownership, and architectural trade-offs. "
        "Master these 3 STAR responses to turn weaknesses into offer letters."
    )

    return InterviewPrepResult(
        roast_id=roast_id,
        candidate_summary=summary,
        questions=questions,
        source="smart_engine",
    )


async def generate_interview_prep(
    roast_data: Dict[str, Any],
    roast_id: str,
    language: str = "en",
) -> InterviewPrepResult:
    """
    Generate tailored interview hot-seat questions and winning STAR responses.
    Uses LLM when available with smart deterministic fallback engine.
    """
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    if not gemini_key and not groq_key:
        return _generate_smart_fallback_questions(roast_data, roast_id, language)

    issues = roast_data.get("issues", [])
    overall_score = roast_data.get("overall_score", 50)
    verdict = roast_data.get("one_line_verdict", "")

    prompt = f"""You are an elite, brutally honest Silicon Valley and top-tier tech Engineering Director and Bar Raiser.
You are reviewing a candidate whose resume scored {overall_score}/100 with verdict: "{verdict}".

The candidate's flagged flaws and weak bullet points are:
{json.dumps(issues[:4], indent=2)}

Predict EXACTLY 3 tough, highly specific interview trap questions an experienced interviewer will ask to test if the candidate is bluffing or lacks depth.
For each question, provide:
1. "flaw_reference": which bullet point triggered this
2. "category": "Metrics & Impact Probe", "Ownership & Conflict", or "System Design & Trade-offs"
3. "difficulty": "Brutal", "Tough", or "Crucial"
4. "question": the exact realistic, probing question
5. "interviewer_trap": what the interviewer is secretly checking
6. "rookie_blunder": the fatal mistake 80% of candidates make when answering
7. "star_framework": {{"situation_task": "...", "action": "...", "result": "..."}}
8. "script_to_say": a crisp, confident spoken answer (under 75 words) that blows the interviewer away.

Return ONLY valid JSON matching this schema:
{{
  "candidate_summary": "<1-2 sentences on what interviewers will target>",
  "questions": [
    {{
      "id": 1,
      "flaw_reference": "...",
      "category": "...",
      "difficulty": "Brutal",
      "question": "...",
      "interviewer_trap": "...",
      "rookie_blunder": "...",
      "star_framework": {{
        "situation_task": "...",
        "action": "...",
        "result": "..."
      }},
      "script_to_say": "..."
    }}
  ]
}}"""

    # 1. Try Gemini
    if gemini_key:
        models = [
            os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            "gemini-1.5-flash",
            "gemini-2.0-flash",
        ]
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.4, "response_mime_type": "application/json"},
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        raw = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                        data = json.loads(raw)
                        return InterviewPrepResult(
                            roast_id=roast_id,
                            candidate_summary=data.get("candidate_summary", ""),
                            questions=[InterviewQuestion(**q) for q in data.get("questions", [])],
                            source="ai",
                        )
            except Exception as e:
                logger.debug(f"Gemini interview prep error with {model}: {e}")

    # Fallback
    return _generate_smart_fallback_questions(roast_data, roast_id, language)
