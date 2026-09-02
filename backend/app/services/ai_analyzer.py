"""
AI analysis service — Hinglish WhatsApp-style Persona
Roasts resumes with savage yet constructive Indian friend energy in natural Hinglish Roman script.
Supports Google Gemini, Groq, Anthropic Claude, and smart fallback engine.
"""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from dotenv import load_dotenv
import httpx

from app.services.extractor import map_quoted_text_to_offsets

load_dotenv()

# ---------------------------------------------------------------------------
# Hinglish Persona System Prompt & Calibration Examples
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a savage but well-meaning Indian friend who's really good at resumes — the kind of friend who roasts you mercilessly in the group chat but also actually helps you fix your life. Write every roast comment in Hinglish (natural WhatsApp-style code-switching between Hindi and English, written in Roman/Latin script, NOT Devanagari), with emojis used naturally like a real person texting, not decoratively.

Tone rules:
- Be funny first, mean never. Roast the RESUME's choices, never the person ("ye bullet point bekaar hai" not "tum bekaar ho").
- Use natural Hinglish rhythm — the way people actually text, not textbook Hindi. Reference: "bhai ye kya likha hai", "iska matlab kya hai yaar", "sach mein itna generic likhoge to", "seedha bolo na kya kiya tha".
- 1-2 emojis per roast line max, placed like a real person texting (end of sentence or after the punchy word), never emoji-spam.
- The "fix" field stays clear and genuinely useful — can still be Hinglish but the actual advice must be concrete and specific, never just a joke.
- Never mock the person's name, college, company, appearance, or anything they didn't choose. Only roast the writing choices on the page.
- "quoted_text" stays in the original language/script of the resume (usually English) — only "roast", "one_line_verdict", and "strengths" entries are Hinglish.

Vocabulary bank — draw from this range, don't reuse the same 2-3 phrases across issues. Mix and match naturally, the way a real person's texting vocabulary shifts sentence to sentence:

Reactions / fillers: arre, arey yaar, bhai, bhai saab, yaar, are baba, haww, ye kya, seriously?, kya baat hai, lo ji, chal hatt, oho, uff, sahi hai bhai (sarcastic), waah (sarcastic), kamaal hai

Disbelief / mock-shock: dimaag kharab hai kya, ye kaise chalega bhai, tujhe pata bhi hai ye kya likha, ye padh ke recruiter bhaag jayega, resume banate waqt so gaye the kya, ye copy-paste lagta hai yaar

Calling something weak/generic: ekdum bekaar, halka hai bhai, isme dum nahi hai, thanda pad gaya ye toh, pheeka hai, generic ki hadd hai, ye toh sabka resume jaisa lag raha hai, kuch alag nahi dikh raha

Asking for specifics: seedha bolo na, exact number batao, kitna kiya bhai numbers mein, thoda specific ho jao, story mat sunao data do, kaam bata na asli mein kya kiya

Approval / when something's actually good: ye theek hai, isko rehne do, ekdum sahi likha hai, ye chalega, badhiya, mast hai ye line, isse copy kar sakte hain baaki jagah bhi

Common WhatsApp-style particles to sprinkle naturally (not every line): yaar, na, bhai, toh, hi, bas, arre, waise

Sentence patterns to vary between (don't always start the same way):
- Question form: "ye kya likha hai bhai?"
- Direct callout: "seedha bolun toh, ye buzzword hai."
- Mock-empathy: "samajh sakta hoon tough tha likhna, par ye nahi chalega."
- Comparison: "baaki sab bhi yahi likhte hain, tum alag kyun nahi ho?"
- Exaggeration for comedy: "isse toh mera 2 line ka resume better hai."

Rotate emoji choice too — don't default to the same 1-2 every time.
Pool: 😩 😭 🤡 💀 😬 🫠 🔥 🙃 😅 🫡 👀 ✋

Note: This is a vocabulary pool, not a script — combine these naturally rather than inserting them verbatim as templates.

CRITICAL ANTI-REPETITION ENFORCEMENT:
Never output the same roast sentence (or a near-identical sentence with only the quoted word swapped) more than once in a single response — even when multiple issues share the same category. If you have three "no-metrics" issues, each of the three roast lines must be built differently: different opening, different joke structure, different vocabulary-bank words, and ideally a reference to something specific in that particular quoted_text (not a generic template that could apply to any missing number).

Before finalizing your response, mentally check: do any two "roast" strings sound like the same sentence with one word changed? If yes, rewrite one of them completely differently.

no-metrics category — rotate between these approaches, don't default to the same one every time:
- Direct question: "Kitna kiya bhai, number bata na."
- Mock-suspicious: "Number nahi hai isme, chhupa kyun rahe ho? 👀"
- Comparison to something concrete: "'Improved performance' — improved kitna, 2% ya 200%? Bahut fark hai bhai."
- Reference the specific skill/tool named in that line: e.g. if the quoted text mentions "LeetCode," joke about that specifically ("LeetCode pe kitne solve kiye, 5 ya 500? Dono alag baat hai") rather than a generic "no number" template — grounding the joke in the actual quoted content is the most reliable way to avoid repetition, since no two quoted lines are identical even when the category is.
- Exaggerated hypothetical: "Isse padh ke lagta hai kaam toh kiya, bas gine nahi kabhi 😅"
- Callback to the fix itself: "Number daal do bas, itna hi kehna hai."

OUTPUT SCHEMA (return exactly this JSON structure):
{
  "overall_score": <integer 0-100>,
  "band": <"weak" | "mid" | "strong">,
  "one_line_verdict": "<string, under 12 words — catchy Hinglish roast headline with 1 emoji>",
  "issues": [
    {
      "quoted_text": "<exact substring from the resume in original text>",
      "category": <"buzzword" | "no-metrics" | "formatting" | "length" | "irrelevant" | "typo" | "other">,
      "roast": "<witty Hinglish WhatsApp-style callout under 25 words with 1-2 emojis>",
      "fix": "<concrete rewrite or specific instruction with clear numbers/examples>"
    }
  ],
  "strengths": ["<short Hinglish bullet with emoji>", ...]
}

CALIBRATION EXAMPLES (STUDY THESE TONES CAREFULLY):

Example 1 (no-metrics & buzzword):
{
  "overall_score": 34,
  "band": "weak",
  "one_line_verdict": "Bhai resume hai ya suspense novel? 🕵️",
  "issues": [
    {
      "quoted_text": "Responsible for building UI components",
      "category": "no-metrics",
      "roast": "\\"Responsible for\\" likhna band karo yaar 😩 recruiter ko number chahiye, kahani nahi.",
      "fix": "Kuch is tarah likho: \\"Built 12 reusable UI components, cutting page load time by 30%\\" — number daalo, impact dikhao."
    },
    {
      "quoted_text": "Worked closely with the design team",
      "category": "buzzword",
      "roast": "\\"Worked closely with\\" — matlab kya kiya bhai? Chai piya ya kuch banaya bhi ☕😂",
      "fix": "Specific batao: \\"Collaborated with 3 designers to ship the checkout redesign, reducing drop-off by 18%.\\""
    }
  ],
  "strengths": [
    "Formatting clean hai, ATS ko padhne mein dikkat nahi hogi 👍"
  ]
}

Example 2 (typos & length):
{
  "overall_score": 42,
  "band": "weak",
  "one_line_verdict": "Design dekh ke aankhon se aansu nikal gaye 😭",
  "issues": [
    {
      "quoted_text": "SKILS: Pythno, Jacascript, C++",
      "category": "typo",
      "roast": "Arre yaar 'Pythno' aur 'Jacascript'? 🤡 Itna jaldi mein the kya ki spellcheck bhi skip kar diya?",
      "fix": "Typo fix karo: 'Python, JavaScript, C++' — submission se pehle ek baar Grammarly ya spellcheck zaroor chalao."
    },
    {
      "quoted_text": "Curriculum Vitae (Page 1 of 4)",
      "category": "length",
      "roast": "4 page ka resume? 💀 Bhai novel likh rahe ho kya? Recruiter 6 second mein band kar dega.",
      "fix": "Isko 1 page (max 2 page agar 5+ years experience hai) mein fit karo. Purani schooling aur obvious baatein hatao."
    }
  ],
  "strengths": [
    "Projects section mein GitHub links live hain 🔥"
  ]
}

Example 3 (irrelevant content & jargon):
{
  "overall_score": 58,
  "band": "mid",
  "one_line_verdict": "Dum hai boss, bas thoda masala kam hai 🍛",
  "issues": [
    {
      "quoted_text": "Hobbies: Playing cricket, listening to music",
      "category": "irrelevant",
      "roast": "Bhai biodata thodi hai 😅 ye hobbies likh ke valuable space kyu waste kar rahe ho?",
      "fix": "Hobbies section hatao aur wahan koi relevant project, hackathon rank ya open-source contribution mention karo."
    },
    {
      "quoted_text": "Utilized cutting-edge synergistic paradigms across teams",
      "category": "buzzword",
      "roast": "Itna bhari corporate jargon padh ke recruiter behosh ho jayega bhai 😵 simple bolo!",
      "fix": "Seedha likho: \\"Led integration of payment gateway across 4 microservices with 99.9% uptime.\\""
    }
  ],
  "strengths": [
    "Career progression ka graph clear dikh raha hai 📈",
    "Section headings crisp aur standard rakhe hain 🎯"
  ]
}

Example 4 (formatting & generic claims):
{
  "overall_score": 64,
  "band": "mid",
  "one_line_verdict": "Acha effort hai yaar, par thoda polishing baaki hai ✨",
  "issues": [
    {
      "quoted_text": "Helped team improve backend stability and performance",
      "category": "no-metrics",
      "roast": "Pheeka lag raha hai bhai 🥱 'Helped team' se credit nahi milta, exact metric batao.",
      "fix": "Rewrite karo: \\"Optimized Redis cache queries, reducing p99 latency from 450ms to 85ms across 12 services.\\""
    },
    {
      "quoted_text": "DECLARATION: I hereby declare all information is true to my knowledge",
      "category": "formatting",
      "roast": "Bhai 2005 ka declaration kyu daal rakha hai? ✋ Modern tech resume mein iski zaroorat nahi hai.",
      "fix": "Declaration section poora delete kardo aur whitespace ko project links ke liye use karo."
    }
  ],
  "strengths": [
    "Tech stack modern hai — FastAPI aur React achha combination hai 🚀",
    "Education details concise aur properly aligned hain 🎓"
  ]
}

SCORING BANDS:
- 0-40: weak — serious buzzwords or lack of numbers
- 41-70: mid — has potential but needs spicy metrics
- 71-100: strong — solid effort, just needs minor polish

Generate 5-8 issues total, ordered from most to least severe. Strengths: 2-3 items."""

USER_PROMPT_TEMPLATE = """Analyze this resume text. Give a brutally honest, funny, WhatsApp-style Hinglish roast with exact quotes and concrete fixes.

--- RESUME START ---
{resume_text}
--- RESUME END ---

Return ONLY the JSON analysis now."""

VALID_BANDS = {"weak", "mid", "strong"}
VALID_CATEGORIES = {
    "buzzword", "no-metrics", "formatting", "length", "irrelevant", "typo", "other"
}

# Hinglish tone markers for quality guard (comprehensive Roman Hinglish pool)
HINGLISH_MARKERS = {
    "bhai", "yaar", "kya", "hai", "ko", "mein", "nahi", "kuch", "matlab", "boss",
    "dekh", "batao", "daalo", "ye", "toh", "bhi", "sirf", "chal", "karo", "hoga",
    "kardo", "rakho", "rahe", "wala", "wali", "thoda", "dum", "sach", "padega",
    "arre", "arey", "baba", "haww", "waah", "kamaal", "bekaar", "halka", "pheeka",
    "seedha", "asli", "theek", "badhiya", "mast", "waise", "dikkat", "aansu",
    "saab", "dimaag", "kharab", "bhaag", "tujhe", "pata", "so", "gaye", "thanda",
    "kitna", "data", "sunao", "rehne", "chahiye", "kahani", "piya", "thodi", "hatao",
    "behosh", "lagta", "chalega", "hatt", "masala", "baaki", "acha", "accha", "kyu",
    "kyun", "pehle", "zaroor", "poora", "baatein"
}


# ---------------------------------------------------------------------------
# Provider 1: Google Gemini (Free API Key from https://aistudio.google.com)
# ---------------------------------------------------------------------------

def _call_gemini_api(api_key: str, resume_text: str) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{SYSTEM_PROMPT}\n\n{USER_PROMPT_TEMPLATE.format(resume_text=resume_text[:12000])}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.7,
        },
    }

    with httpx.Client(timeout=45.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return _extract_json(raw_text)


# ---------------------------------------------------------------------------
# Provider 2: Groq (Free API Key from https://console.groq.com)
# ---------------------------------------------------------------------------

def _call_groq_api(api_key: str, resume_text: str) -> dict:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT_TEMPLATE.format(resume_text=resume_text[:12000])},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.7,
    }

    with httpx.Client(timeout=45.0) as client:
        response = client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        raw_text = data["choices"][0]["message"]["content"]
        return _extract_json(raw_text)


# ---------------------------------------------------------------------------
# Provider 3: Anthropic Claude
# ---------------------------------------------------------------------------

def _call_anthropic_api(api_key: str, resume_text: str) -> dict:
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key, timeout=45.0)
    user_message = USER_PROMPT_TEMPLATE.format(resume_text=resume_text[:12000])
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
        temperature=0.7,
    )
    raw_text = response.content[0].text
    return _extract_json(raw_text)


# ---------------------------------------------------------------------------
# Fallback Roast Generator in Authentic Hinglish
# ---------------------------------------------------------------------------

def _generate_fallback_roast(resume_text: str) -> dict[str, Any]:
    """
    Intelligent heuristic fallback analyzer with hilarious WhatsApp-style Hinglish tone.
    Quotes actual candidate lines and generates shareable Hinglish roasts from vocabulary pool.
    """
    lines = [
        line.strip() for line in resume_text.splitlines()
        if len(line.strip()) > 20 and not line.strip().startswith("http")
    ]

    issues = []
    buzzwords = [
        ("responsible for", "no-metrics", "\"Responsible for\" likhna band karo yaar 😩 recruiter ko number chahiye, kahani nahi.", "Kuch is tarah likho: 'Built 12 reusable UI components, cutting page load time by 30%' — number daalo, impact dikhao."),
        ("worked closely with", "buzzword", "\"Worked closely with\" — matlab kya kiya bhai? Chai piya ya kuch banaya bhi ☕😂", "Specific batao: 'Collaborated with 3 designers to ship checkout redesign, reducing drop-off by 18%.'"),
        ("synerg", "buzzword", "Bhai itna heavy buzzword padhke recruiter ka sar ghoom jayega 😵 seedhi baat karo na!", "Corporate jargon cut karo aur exact tools/outcomes list karo."),
        ("spearheaded", "buzzword", "\"Spearheaded\" har doosre resume mein milta hai bhai 🥱 kuch fresh aur real likho.", "Action-first likho: 'Led a team of 4 to architect the notification engine from scratch.'"),
        ("passionate", "buzzword", "\"Passionate professional\" likhne se shortlist nahi hoga boss 🤷‍♂️ kaam se prove karo.", "Adjectives hatao aur shipped projects ke live metrics daalo."),
        ("assisted", "no-metrics", "\"Assisted\" likh ke credit kyu gawa rahe ho yaar? Apna contribution front foot pe rakho 🏏", "Rewrite karo: 'Resolved 45+ critical production bugs in PostgreSQL, reducing ticket backlog by 40%.'"),
        ("curriculum vitae", "length", "CV header likh ke space waste mat karo bhai 💀 direct naam aur role daalo.", "Header clean karo: Top pe 'Full Stack Engineer' aur LinkedIn/GitHub link rakho."),
        ("declaration", "irrelevant", "Bhai 2012 ka format abhi tak chala rahe ho kya? 💀 Declaration koi nahi padhta.", "Ye section delete kardo aur resume ka vertical whitespace save karo."),
        ("hobbies", "irrelevant", "Bhai biodata thodi hai 😅 ye hobbies likh ke valuable space kyu waste kar rahe ho?", "Hobbies hatao aur hackathon rank ya open-source contribution mention karo."),
    ]

    for line in lines:
        lower = line.lower()
        for bw, cat, roast_txt, fix_txt in buzzwords:
            if bw in lower and len(issues) < 6:
                if not any(iss["quoted_text"] == line[:110] for iss in issues):
                    issues.append({
                        "quoted_text": line[:110],
                        "category": cat,
                        "roast": roast_txt,
                        "fix": fix_txt,
                    })
                break

    # Numberless bullet check
    if len(issues) < 4:
        for line in lines:
            if not any(char.isdigit() for char in line) and len(line) > 35 and len(issues) < 6:
                if not any(iss["quoted_text"] == line[:110] for iss in issues):
                    issues.append({
                        "quoted_text": line[:110],
                        "category": "no-metrics",
                        "roast": "Is line mein ek bhi number nahi hai bhai! Recruiter ko kaise pata chalega kitna kaam kiya? 📉",
                        "fix": "Quantify karo: 'Scaled server throughput by 35% handling 50,000+ requests/min.'",
                    })

    # Typos check in skills or text
    for line in lines:
        lower = line.lower()
        if any(mis in lower for mis in ["skils", "pythno", "javascrip", "mangment", "experiance"]):
            issues.append({
                "quoted_text": line[:100],
                "category": "typo",
                "roast": "Arre yaar spelling mistake? 🤡 Itna jaldi mein the kya ki spellcheck bhi skip kar diya?",
                "fix": "Typo fix karo aur submission se pehle spellcheck zaroor run karo.",
            })
            break

    if not issues:
        sample_line = lines[0] if lines else "Experienced Software Developer"
        issues.append({
            "quoted_text": sample_line[:100],
            "category": "buzzword",
            "roast": "Thoda generic lag raha hai bhai, padh ke lagta hai template se uthaya hai 📋😴",
            "fix": "Apne core stack aur standout accomplishments ko highlight karo.",
        })

    score = 38 if len(issues) >= 4 else 56
    band = "weak" if score <= 40 else "mid"

    verdicts = [
        "Bhai resume hai ya suspense novel? 🕵️",
        "Dum hai boss, bas thoda masala aur metrics kam hain 🍛",
        "Acha effort hai yaar, par buzzwords zyada bhar diye hain 🤖",
        "Design dekh ke aankhon se aansu nikal gaye 😭",
    ]
    verdict = verdicts[len(lines) % len(verdicts)]

    strengths = [
        "Formatting overall clean hai boss, ATS ko padhne mein asani hogi 👍",
        "Core technical domain samajh aa raha hai, bas thodi polishing chahiye 🚀",
    ]

    return {
        "overall_score": score,
        "band": band,
        "one_line_verdict": verdict,
        "issues": issues,
        "strengths": strengths,
    }


def _has_hinglish_tone(text: str) -> bool:
    """Check whether a text string contains natural Hinglish markers."""
    if not text:
        return False
    words = re.findall(r"[a-zA-Z]+", text.lower())
    return any(w in HINGLISH_MARKERS for w in words)


def _validate_schema(data: dict, resume_text: str | None = None) -> None:
    required_top = {"overall_score", "band", "one_line_verdict", "issues", "strengths"}
    missing = required_top - set(data.keys())
    if missing:
        raise ValueError(f"Missing top-level keys: {missing}")

    score = data["overall_score"]
    if not isinstance(score, int) or not (0 <= score <= 100):
        if isinstance(score, (float, str)):
            try:
                data["overall_score"] = int(float(score))
            except Exception:
                raise ValueError(f"overall_score must be integer 0-100, got {score!r}")
        else:
            raise ValueError(f"overall_score must be integer 0-100, got {score!r}")

    band = str(data.get("band", "")).lower().strip()
    if band not in VALID_BANDS:
        if data["overall_score"] <= 40:
            data["band"] = "weak"
        elif data["overall_score"] <= 70:
            data["band"] = "mid"
        else:
            data["band"] = "strong"
    else:
        data["band"] = band

    # Tone check on one_line_verdict
    verdict = str(data.get("one_line_verdict", ""))
    if not verdict:
        raise ValueError("one_line_verdict cannot be empty")

    if not isinstance(data["issues"], list) or len(data["issues"]) < 1:
        raise ValueError("issues must be a non-empty list")

    validated_issues = []
    hinglish_roast_count = 0
    resume_lower = resume_text.lower() if resume_text else None
    resume_norm = re.sub(r"\s+", " ", resume_text).lower() if resume_text else None

    for issue in data["issues"]:
        if not isinstance(issue, dict):
            continue
        for field in ("quoted_text", "category", "roast", "fix"):
            if field not in issue or not isinstance(issue[field], str):
                issue[field] = str(issue.get(field, ""))
        cat = str(issue["category"]).lower().strip()
        if cat not in VALID_CATEGORIES:
            issue["category"] = "other"
        else:
            issue["category"] = cat

        # Verify quoted text is non-trivial
        q_text = issue["quoted_text"].strip().strip('"\'')
        if not q_text or len(q_text) < 3:
            continue

        # If resume_text is provided, verify quoted_text is grounded in the original resume
        if resume_lower and resume_norm:
            q_lower = q_text.lower()
            q_norm = re.sub(r"\s+", " ", q_lower)
            if q_lower not in resume_lower and q_norm not in resume_norm:
                # Check first 25 characters if long quote
                if len(q_lower) > 25 and q_lower[:25] not in resume_lower:
                    # Drop ungrounded / hallucinated quote if not found in resume
                    continue

        if _has_hinglish_tone(issue["roast"]):
            hinglish_roast_count += 1

        validated_issues.append(issue)

    if not validated_issues:
        raise ValueError("No valid grounded issues found in analysis")

    # Tone guard: At least one roast or the verdict must have authentic Hinglish markers
    if hinglish_roast_count == 0 and not _has_hinglish_tone(verdict):
        raise ValueError("AI response failed Hinglish tone check — missing conversational Hinglish markers")

    data["issues"] = validated_issues

    if not isinstance(data["strengths"], list):
        data["strengths"] = [str(data["strengths"])] if data["strengths"] else []



def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*$", "", text, flags=re.IGNORECASE)
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in AI response")
    return json.loads(text[start : end + 1])


def _find_duplicate_roasts(issues: list[dict], threshold: float = 0.85) -> list[tuple[int, str, str]]:
    """
    Identifies pairwise duplicate or near-identical roast strings (>85% similarity).
    Returns list of (index, quoted_text, duplicate_roast).
    """
    import difflib
    duplicates: list[tuple[int, str, str]] = []
    seen_norms: list[tuple[str, int]] = []

    for idx, iss in enumerate(issues):
        roast = iss.get("roast", "")
        norm = re.sub(r"[^a-z0-9]", "", roast.lower())
        if not norm:
            continue

        is_dup = False
        for prev_norm, _ in seen_norms:
            ratio = difflib.SequenceMatcher(None, norm, prev_norm).ratio()
            if ratio >= threshold:
                is_dup = True
                break

        if is_dup:
            duplicates.append((idx, iss.get("quoted_text", ""), roast))
        else:
            seen_norms.append((norm, idx))

    return duplicates


def _deduplicate_roasts(data: dict) -> None:
    """
    Lightweight server-side safety net (Section 3.7).
    Compares all roast strings pairwise using normalized string similarity (>85%).
    If duplicates remain after retry, substitutes the duplicate with varied Hinglish phrasing from pool.
    """
    import difflib

    issues = data.get("issues", [])
    if len(issues) <= 1:
        return

    varied_no_metrics = [
        "Kitna kiya bhai, exact number bata na yaar 😩 suspense mat banao.",
        "Number nahi hai isme bhai, chhupa kyun rahe ho? 👀 Data dikhao!",
        "'Improved performance' — improved kitna, 2% ya 200%? Bahut fark hai bhai 📉",
        "Isse padh ke lagta hai kaam toh kiya, bas gine nahi kabhi 😅",
        "Number daal do bas, itna hi kehna hai — bina metrics ke credit nahi milta 📊",
        "Seedha bolo na kitna scale kiya, kahani mat sunao data do 📈",
    ]

    varied_buzzword = [
        "Ye buzzword line sab copy karte hain bhai 💀 kuch apna real kaam likho.",
        "Corporate jargon padh ke recruiter ka dimaag ghoom jayega 😵 seedhi baat karo!",
        "Thoda generic lag raha hai bhai, padh ke lagta hai template se uthaya hai 📋😴",
        "Seedha bolo na kya kiya tha — itna ghumane ki zaroorat nahi hai 🤷‍♂️",
        "Pheeka lag raha hai ye line boss, asli impact front foot pe dikhao 🏏",
    ]

    seen_norms: list[tuple[str, int]] = []

    for idx, iss in enumerate(issues):
        roast = iss.get("roast", "")
        norm = re.sub(r"[^a-z0-9]", "", roast.lower())
        if not norm:
            continue

        is_dup = False
        for prev_norm, _ in seen_norms:
            ratio = difflib.SequenceMatcher(None, norm, prev_norm).ratio()
            if ratio >= 0.85:
                is_dup = True
                break

        if is_dup:
            cat = iss.get("category", "")
            if cat == "no-metrics":
                alt = varied_no_metrics[idx % len(varied_no_metrics)]
            else:
                alt = varied_buzzword[idx % len(varied_buzzword)]
            safe_orig = roast.encode("ascii", "replace").decode("ascii")
            safe_alt = alt.encode("ascii", "replace").decode("ascii")
            print(f"[INFO] Server-side duplicate roast detected & replaced for issue #{idx+1}: {safe_orig!r} -> {safe_alt!r}")
            iss["roast"] = alt
            norm = re.sub(r"[^a-z0-9]", "", alt.lower())

        seen_norms.append((norm, idx))


# ---------------------------------------------------------------------------
# Main Router
# ---------------------------------------------------------------------------

def analyze_resume(resume_text: str) -> dict[str, Any]:
    """
    Analyzes resume using available provider with Hinglish roast persona:
    1. GEMINI_API_KEY (Google Gemini Free)
    2. GROQ_API_KEY (Groq Free)
    3. ANTHROPIC_API_KEY (Claude)
    4. Heuristic Hinglish Fallback
    """
    if not resume_text or len(resume_text.strip()) < 80:
        raise ValueError("That doesn't look like a full resume — upload the whole document.")

    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    load_dotenv(dotenv_path=os.path.abspath(env_path), override=True)

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    data: dict | None = None

    # 1. Try Google Gemini
    if gemini_key:
        try:
            data = _call_gemini_api(gemini_key, resume_text)
            _validate_schema(data, resume_text)
        except Exception as e:
            print(f"[WARN] Gemini API error: {e}")

    # 2. Try Groq
    if not data and groq_key:
        try:
            data = _call_groq_api(groq_key, resume_text)
            _validate_schema(data, resume_text)
        except Exception as e:
            print(f"[WARN] Groq API error: {e}")

    # 3. Try Anthropic Claude
    if not data and anthropic_key:
        try:
            data = _call_anthropic_api(anthropic_key, resume_text)
            _validate_schema(data, resume_text)
        except Exception as e:
            print(f"[WARN] Anthropic API error: {e}")

    # 4. Fallback if external API calls fail
    if not data:
        data = _generate_fallback_roast(resume_text)

    # Server-side anti-repetition / duplicate check safety net (Section 3.7)
    _deduplicate_roasts(data)

    # Map offsets safely
    quoted_texts = [iss["quoted_text"] for iss in data["issues"]]
    offsets = map_quoted_text_to_offsets(quoted_texts, resume_text)

    for i, issue in enumerate(data["issues"]):
        issue["start_offset"], issue["end_offset"] = offsets[i]
        issue["severity_rank"] = i + 1

    return data
