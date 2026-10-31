"""
AI Resume Bullet Rewriter Service
Transforms weak, passive, or vague resume bullet points into high-impact,
quantified STAR-method (Situation, Task, Action, Result) accomplishments.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import List, Optional
from pydantic import BaseModel, Field
import httpx

logger = logging.getLogger(__name__)


class BulletRewriteOption(BaseModel):
    style: str = Field(description="Style name: 'Impact & Metrics (STAR)', 'Action & Leadership', or 'ATS-Optimized Concise'")
    badge: str = Field(description="Short badge label like 'STAR Method', 'High Initiative', 'ATS Scannable'")
    rewritten_text: str = Field(description="The rewritten high-converting bullet point")
    explanation: str = Field(description="Why this version performs better with recruiters")


class BulletRewriteResult(BaseModel):
    original: str
    target_role: Optional[str] = None
    options: List[BulletRewriteOption]
    source: str = "ai"  # 'ai' or 'fallback'


def _fallback_bullet_rewrite(original: str, target_role: Optional[str] = None) -> BulletRewriteResult:
    """Deterministic fallback rewrites when external AI is unavailable or rate-limited."""
    clean = original.strip().rstrip(".")
    role_ctx = f" for {target_role}" if target_role else ""

    return BulletRewriteResult(
        original=original,
        target_role=target_role,
        source="fallback",
        options=[
            BulletRewriteOption(
                style="Impact & Metrics (STAR)",
                badge="STAR Method",
                rewritten_text=f"Spearheaded execution{role_ctx}, optimizing critical workflows and driving a 30%+ improvement in overall operational efficiency.",
                explanation="Adds quantifiable impact (30%+) and an authoritative action verb ('Spearheaded') replacing vague phrasing.",
            ),
            BulletRewriteOption(
                style="Action & Leadership",
                badge="High Initiative",
                rewritten_text=f"Led end-to-end delivery of core deliverables{role_ctx}, collaborating across cross-functional teams to streamline turnaround time by 25%.",
                explanation="Highlights ownership, cross-team collaboration, and measurable turnaround reduction.",
            ),
            BulletRewriteOption(
                style="ATS-Optimized Concise",
                badge="ATS Scannable",
                rewritten_text=f"Architected and deployed scalable solutions{role_ctx}, ensuring 99.9% reliability while adhering to industry best practices.",
                explanation="Packed with high-density technical keywords and reliability metrics that automated ATS scanners prioritize.",
            ),
        ],
    )


async def rewrite_bullet(
    bullet: str,
    target_role: Optional[str] = None,
    language: str = "en",
) -> BulletRewriteResult:
    """Generate 3 professional STAR-framework rewrites for a resume bullet point."""
    if not bullet or len(bullet.strip()) < 5:
        return _fallback_bullet_rewrite(bullet or "Assisted with various tasks", target_role)

    gemini_key = os.getenv("GEMINI_API_KEY")
    groq_key = os.getenv("GROQ_API_KEY")

    if not gemini_key and not groq_key:
        return _fallback_bullet_rewrite(bullet, target_role)

    prompt = f"""You are an elite executive resume writer and ATS optimization specialist.
Rewrite the following weak, vague, or passive resume bullet point into 3 distinctly styled, high-converting bullet points following the STAR (Situation, Task, Action, Result) methodology.

Original Bullet:
"{bullet}"
{f"Target Role / Specialty: {target_role}" if target_role else ""}

Guidelines:
1. Always start with a strong, active power verb (e.g., Architected, Spearheaded, Engineered, Orchestrated, Overhauled, Accelerated). Avoid weak verbs like 'Assisted', 'Helped', 'Worked on', 'Responsible for'.
2. Inject realistic, plausible quantifiable metrics (e.g., percentages, latencies, cost savings, user counts) that illustrate measurable business impact.
3. Keep each rewrite to 1-2 punchy lines suitable for a tech/corporate resume.
4. Provide exactly 3 options:
   - Option 1: Style: 'Impact & Metrics (STAR)', Badge: 'STAR Method'
   - Option 2: Style: 'Action & Leadership', Badge: 'High Initiative'
   - Option 3: Style: 'ATS-Optimized Concise', Badge: 'ATS Scannable'

Return STRICT JSON matching this schema with NO markdown code fences:
{{
  "options": [
    {{
      "style": "Impact & Metrics (STAR)",
      "badge": "STAR Method",
      "rewritten_text": "...",
      "explanation": "..."
    }},
    {{
      "style": "Action & Leadership",
      "badge": "High Initiative",
      "rewritten_text": "...",
      "explanation": "..."
    }},
    {{
      "style": "ATS-Optimized Concise",
      "badge": "ATS Scannable",
      "rewritten_text": "...",
      "explanation": "..."
    }}
  ]
}}"""

    # Try Gemini if key is available
    if gemini_key:
        models_to_try = [
            os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            "gemini-1.5-flash",
            "gemini-2.0-flash",
        ]
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.5,
                "maxOutputTokens": 1024,
            },
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            for model in list(dict.fromkeys(models_to_try)):
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                try:
                    resp = await client.post(url, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                        clean_json = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
                        clean_json = re.sub(r"```$", "", clean_json.strip(), flags=re.MULTILINE).strip()
                        parsed = json.loads(clean_json)
                        opts = parsed.get("options", [])
                        if len(opts) >= 3:
                            return BulletRewriteResult(
                                original=bullet,
                                target_role=target_role,
                                options=[BulletRewriteOption(**o) for o in opts[:3]],
                                source="ai",
                            )
                except Exception as e:
                    logger.warning(f"Gemini rewrite failed on {model}: {e}")

    return _fallback_bullet_rewrite(bullet, target_role)
