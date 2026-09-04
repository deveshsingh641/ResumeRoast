"""
Battle Analysis Service — Head-to-Head Resume Roast Comparison.
Takes structured JSON outputs from two resumes and produces savage comparative commentary.
"""
from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from dotenv import load_dotenv
import httpx

logger = logging.getLogger(__name__)

from app.i18n.mapping import DEFAULT_LANGUAGE, normalize_language
from app.prompts import get_battle_system_prompt
from app.services.ai_analyzer import _extract_json

load_dotenv()


def _generate_fallback_battle(f1: dict, f2: dict, language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    """Deterministic fallback comparator if external AI call is unavailable."""
    lang = normalize_language(language)
    s1 = f1.get("overall_score", 50)
    s2 = f2.get("overall_score", 50)
    diff = s1 - s2

    if lang == "hi-IN":
        if abs(diff) < 5:
            winner = "draw"
            margin = "draw"
            verdict = f"Dono ka haal lagbhag ek jaisa hai bhai! 🤝 Fighter 1 ka score {s1} aur Fighter 2 ka {s2}. Dono ko metrics daalne ki sakht zaroorat hai."
        elif s1 > s2:
            winner = "fighter_1"
            margin = "landslide" if diff > 20 else "close"
            verdict = f"Fighter 1 ne Fighter 2 ko dho diya! 🥊 Score {s1} vs {s2}. Fighter 2 ke resume mein buzzwords itne hain ki ATS bhi behosh ho gaya."
        else:
            winner = "fighter_2"
            margin = "landslide" if abs(diff) > 20 else "close"
            verdict = f"Fighter 2 ne baazi maar li! 🏆 Score {s2} vs {s1}. Fighter 1 ka resume padhke lagta hai 2010 ka biodata dekh rahe hain."
        f1_roast = f1.get("issues", [{}])[0].get("roast", f1.get("one_line_verdict", "Format theek hai par numbers gayab hain."))
        f2_roast = f2.get("issues", [{}])[0].get("roast", f2.get("one_line_verdict", "Thoda aur concrete kaam dikhana padega."))
    else:
        if abs(diff) < 5:
            winner = "draw"
            margin = "draw"
            verdict = f"It's a dead heat! 🤝 Fighter 1 scored {s1} and Fighter 2 scored {s2}. Both candidates need to stop relying on adjectives and put real metrics on the page."
        elif s1 > s2:
            winner = "fighter_1"
            margin = "landslide" if diff > 20 else "close"
            verdict = f"Fighter 1 takes the match! 🥊 Score {s1} vs {s2}. Fighter 2's resume had so much corporate fluff that even an ATS parser gave up."
        else:
            winner = "fighter_2"
            margin = "landslide" if abs(diff) > 20 else "close"
            verdict = f"Fighter 2 wins the duel! 🏆 Score {s2} vs {s1}. Fighter 1's resume reads like a generic job description from a decade ago."
        f1_roast = f1.get("issues", [{}])[0].get("roast", f1.get("one_line_verdict", "Clean structure, but metrics are missing."))
        f2_roast = f2.get("issues", [{}])[0].get("roast", f2.get("one_line_verdict", "Needs more concrete, quantifiable accomplishments."))

    return {
        "winner": winner,
        "margin": margin,
        "verdict": verdict,
        "fighter_1_best_line": f1_roast,
        "fighter_2_best_line": f2_roast,
    }


def analyze_battle(f1: dict, f2: dict, language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    """Compare two structured resume analyses using LLM or fallback."""
    lang = normalize_language(language)
    battle_system_prompt = get_battle_system_prompt(lang)

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    prompt_content = f"""
FIGHTER 1 ANALYSIS:
Score: {f1.get('overall_score')}/100 ({f1.get('band')})
Verdict: {f1.get('one_line_verdict')}
Top Issues: {json.dumps(f1.get('issues', [])[:3])}
Strengths: {json.dumps(f1.get('strengths', []))}

FIGHTER 2 ANALYSIS:
Score: {f2.get('overall_score')}/100 ({f2.get('band')})
Verdict: {f2.get('one_line_verdict')}
Top Issues: {json.dumps(f2.get('issues', [])[:3])}
Strengths: {json.dumps(f2.get('strengths', []))}

Declare the winner and generate the savage comparative JSON verdict now.
"""

    # 1. Gemini
    if gemini_key:
        candidate_models = [os.getenv("GEMINI_MODEL", "gemini-3.6-flash"), "gemini-flash-latest"]
        for model in candidate_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                payload = {
                    "contents": [
                        {"parts": [{"text": f"{battle_system_prompt}\n\n{prompt_content}"}]}
                    ],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.7},
                }
                with httpx.Client(timeout=30.0) as client:
                    res = client.post(url, json=payload)
                    if res.status_code == 404:
                        continue
                    res.raise_for_status()
                    raw_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    data = _extract_json(raw_text)
                    if "winner" in data and "verdict" in data:
                        return data
            except Exception as e:
                logger.debug(f"Gemini battle error on model {model}: {e}")

    # 2. Groq
    if groq_key:
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"}
            payload = {
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": battle_system_prompt},
                    {"role": "user", "content": prompt_content},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7,
            }
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                raw_text = res.json()["choices"][0]["message"]["content"]
                data = _extract_json(raw_text)
                if "winner" in data and "verdict" in data:
                    return data
        except Exception as e:
            print(f"[WARN] Groq battle error: {e}")

    # 3. Fallback
    return _generate_fallback_battle(f1, f2, language=lang)
