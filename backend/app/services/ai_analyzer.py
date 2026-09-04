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
from app.services.anti_repeat_service import anti_repeat_memory, BASELINE_JOKE_BANKS

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

MANDATORY ACCURACY CHECK — DO THIS BEFORE ASSIGNING ANY CATEGORY:
For every line you plan to flag, re-read the EXACT quoted_text you have copied from the resume:

1. "no-metrics" is ONLY valid if quoted_text contains ZERO digits (0–9), ZERO percentage signs, ZERO counts, and ZERO spelled-out numbers (one, two, three, four, five, six, seven, eight, nine, ten, first, second, third). If the line already contains a number — ANY number — "no-metrics" CANNOT apply. Either find a different genuine flaw (buzzword, vague language, irrelevant) or skip that line entirely.

2. Every "roast" field MUST be grounded in the specific quoted_text. It must reference an actual word, phrase, tool name, or claim from that exact line. Self-test before writing: "Could I copy this roast sentence under a completely different issue and it would still make sense?" If yes → it is too generic → rewrite it to be specific to this line.

3. Before finalizing the full response, read all roast strings together. If any two sound like the same sentence with one word swapped → rewrite one of them completely using a different structure, different vocabulary, and a different reference to its specific quoted_text.

CRITICAL ANTI-REPETITION ENFORCEMENT & DEDICATED CATEGORY JOKE BANKS:
Never output the same roast sentence (or a near-identical sentence with only the quoted word swapped) more than once in a single response — even when multiple issues share the same category. If you have three "no-metrics" issues, each of the three roast lines must be built differently: different opening, different joke structure, different vocabulary-bank words, and ideally a reference to something specific in that particular quoted_text (not a generic template that could apply to any missing number).

Rotate between these dedicated category joke banks and phrasing styles:

no-metrics category (at least 8 styles):
- "Kitna kiya bhai, number bata na."
- "Number nahi hai isme, chhupa kyun rahe ho? 👀"
- "'Improved performance' — improved kitna, 2% ya 200%? Bahut fark hai bhai."
- Reference the specific tool/skill named in that exact quoted line: e.g. if the quoted text mentions "LeetCode," joke about that specifically ("LeetCode pe kitne solve kiye, 5 ya 500? Dono alag baat hai") rather than a generic template — grounding the joke in the actual quoted content is the most reliable way to avoid repetition, since no two quoted lines are identical even when the category is.
- "Isse padh ke lagta hai kaam toh kiya, bas gine nahi kabhi 😅"
- "Number daal do bas, itna hi kehna hai."
- "Bina number ke ye line resume mein hai ya shayari mein, samajh nahi aa raha 📝"
- "Data do yaar, story nahi chahiye humein 📊"

buzzword category (dedicated pool, at least 8 styles):
- "Ye word har second resume mein hai bhai, tu unique kaise banega isse?"
- "Buzzword daal diya, ab kaam bhi dikha do na."
- "Ye line copy-paste lagti hai, LinkedIn se utha li kya? 😅"
- "Itna generic hai ye, isse toh weather report zyada specific hoti hai."
- "Ye word suna-suna sa lagta hai bhai, naya kuch socho."
- "Har resume mein ye milega, tu bhi unme se ek lag raha hai abhi."
- "Sabko pata hai tu ye ho, likhna zaroori nahi tha 🙃"
- "Ye adjective proof nahi maangta, achievement maangta hai."

formatting category (at least 6 styles):
- "Spacing dekh ke lag raha hai jaldi mein banaya tha resume 😬"
- "Font size itni chhoti hai, recruiter chashma dhundhega 🔍"
- "Alignment off hai bhai, ye resume hai ya jigsaw puzzle?"
- "Itne fonts use kar diye, ransom note jaisa lag raha hai 🗞️"
- "Bullet points ka size hi consistent nahi hai yaar."
- "Margins itne tight hain, resume saans nahi le pa raha 😮💨"

length category (at least 6 styles):
- "Itna lamba kar diya, recruiter ke paas PhD karne ka time nahi hai isko padhne ke liye 📚"
- "Ek page mein sab thoonsa hua hai, Diwali ke baad ka WhatsApp status jaisa lag raha hai 🪔"
- "Bahut kuch likh diya, matlab kuch nahi mila padhne ko."
- "Itni detail kisi ko nahi chahiye bhai, seedha point pe aao."
- "Recruiter 6 second dekhta hai resume, tune usse 6 page bana diya."
- "Chota aur sharp likho, ye essay nahi hai."

irrelevant category (at least 6 styles):
- "Ye yahan kyun hai bhai? Iska job se koi lena dena nahi 🤔"
- "College fest mein volunteer kiya tha, but yahan uska kya kaam?"
- "Ye detail resume mein daalna zaroori tha kya, seriously?"
- "Iska is role se koi connection nahi bhai, hata do."
- "Recruiter ko iske baare mein janna hi nahi hai."
- "Space waste ho raha hai is line pe, kuch relevant daalo."

typo category (at least 5 styles):
- "Spelling mistake hai bhai, spellcheck bhi nahi chalaya kya? 😩"
- "Ek typo dikh gaya, recruiter ko lagega detail-oriented nahi ho."
- "Ye galti chhoti lagti hai but bahut bada impression banati hai galat."
- "Proofread karna bhool gaye kya, ek baar aur padh lo."
- "Chhoti si galti hai, but recruiter ki nazar pehle yahi jaati hai."

other category (flexible catch-all, at least 5 styles):
- "Ye line samajh nahi aayi bhai, tum khud padh ke bataoge?"
- "Kuch toh gadbad hai isme, par pin nahi kar pa raha exactly kya."
- "Ye reh gaya explain kiye bina, thoda clarify karo."
- "Iska matlab nikal nahi raha, seedha likho."
- "Ye jagah out of place lag rahi hai bhai."

Before finalizing your response, mentally check: do any two "roast" strings sound like the same sentence with one word changed? If yes, rewrite one of them completely differently.

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

{exclusion_block}

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

def _call_gemini_api(api_key: str, resume_text: str, exclusion_block: str = "") -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    formatted_user_prompt = USER_PROMPT_TEMPLATE.format(
        resume_text=resume_text[:12000],
        exclusion_block=f"\n{exclusion_block}\n" if exclusion_block else "",
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{SYSTEM_PROMPT}\n\n{formatted_user_prompt}"
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

def _call_groq_api(api_key: str, resume_text: str, exclusion_block: str = "") -> dict:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    formatted_user_prompt = USER_PROMPT_TEMPLATE.format(
        resume_text=resume_text[:12000],
        exclusion_block=f"\n{exclusion_block}\n" if exclusion_block else "",
    )
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": formatted_user_prompt},
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

def _call_anthropic_api(api_key: str, resume_text: str, exclusion_block: str = "") -> dict:
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key, timeout=45.0)
    formatted_user_prompt = USER_PROMPT_TEMPLATE.format(
        resume_text=resume_text[:12000],
        exclusion_block=f"\n{exclusion_block}\n" if exclusion_block else "",
    )
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": formatted_user_prompt}],
        temperature=0.7,
    )
    raw_text = response.content[0].text
    return _extract_json(raw_text)


# ---------------------------------------------------------------------------
# Fallback Roast Generator in Authentic Hinglish
# ---------------------------------------------------------------------------

def _generate_fallback_roast(resume_text: str, exclusion_block: str = "") -> dict[str, Any]:
    """
    Intelligent heuristic fallback analyzer with hilarious WhatsApp-style Hinglish tone.
    Quotes actual candidate lines and generates shareable Hinglish roasts from vocabulary pool,
    actively avoiding recently used lines.
    """
    import random
    lines = [
        line.strip() for line in resume_text.splitlines()
        if len(line.strip()) > 20 and not line.strip().startswith("http")
    ]

    recent_exclusions = set(anti_repeat_memory.get_recent_roasts())
    used_roasts: set[str] = set()

    KNOWN_TOOLS = [
        "react", "python", "javascript", "typescript", "api", "graphql", "aws", "gcp",
        "docker", "kubernetes", "postgres", "sql", "redis", "kafka", "spark", "flutter",
        "swift", "cypress", "selenium", "node", "java", "c++", "go", "ci/cd", "etl",
        "linux", "cloud", "ui", "database", "backend", "frontend", "devops",
    ]

    def _extract_tool(text: str) -> str | None:
        t_lower = text.lower()
        for t in KNOWN_TOOLS:
            if re.search(rf"\b{re.escape(t)}\b", t_lower):
                return t
        return None

    def _select_roast(cat: str, line_quote: str, fallback_default: str) -> str:
        tool = _extract_tool(line_quote)
        grounded_options = []

        if tool:
            t_name = tool.title()
            if cat == "no-metrics":
                grounded_options = [
                    f"'{t_name}' pe kaam kiya, par kitne users ya requests handle kiye? Number bata na.",
                    f"'{t_name}' mein performance kitni improve hui bhai? 2% ya 200%? Data do 📊",
                    f"'{t_name}' use kiya sahi hai, par scale kitna kiya bhai? Numbers chhupa kyun rahe ho? 👀",
                    f"'{t_name}' ke saath exact metric daal do bas — bina data ke credit nahi milta 📉",
                ]
            elif cat == "buzzword":
                grounded_options = [
                    f"'{t_name}' ke saath itna heavy buzzword daal diya, ab concrete kaam bhi dikha do na.",
                    f"Har resume mein '{t_name}' ke aage yahi generic line milti hai bhai, tu unique kaise banega?",
                    f"'{t_name}' use kiya achha hai, par ye line copy-paste lagti hai LinkedIn se 😅",
                ]

        pool = list(BASELINE_JOKE_BANKS.get(cat, BASELINE_JOKE_BANKS["other"]))
        combined = grounded_options + pool
        candidates = [r for r in combined if r not in used_roasts and r not in recent_exclusions]
        if not candidates:
            candidates = [r for r in combined if r not in used_roasts]
        chosen = random.choice(candidates) if candidates else fallback_default
        used_roasts.add(chosen)
        return chosen

    issues = []
    buzzwords = [
        ("responsible for", "no-metrics", "Kuch is tarah likho: 'Built 12 reusable UI components, cutting page load time by 30%' — number daalo, impact dikhao."),
        ("worked closely with", "buzzword", "Specific batao: 'Collaborated with 3 designers to ship checkout redesign, reducing drop-off by 18%.'"),
        ("synerg", "buzzword", "Corporate jargon cut karo aur exact tools/outcomes list karo."),
        ("spearheaded", "buzzword", "Action-first likho: 'Led a team of 4 to architect the notification engine from scratch.'"),
        ("passionate", "buzzword", "Adjectives hatao aur shipped projects ke live metrics daalo."),
        ("assisted", "no-metrics", "Rewrite karo: 'Resolved 45+ critical production bugs in PostgreSQL, reducing ticket backlog by 40%.'"),
        ("curriculum vitae", "length", "Header clean karo: Top pe 'Full Stack Engineer' aur LinkedIn/GitHub link rakho."),
        ("declaration", "irrelevant", "Ye section delete kardo aur resume ka vertical whitespace save karo."),
        ("hobbies", "irrelevant", "Hobbies hatao aur hackathon rank ya open-source contribution mention karo."),
    ]

    for line in lines:
        lower = line.lower()
        for bw, cat, fix_txt in buzzwords:
            if bw in lower and len(issues) < 6:
                if not any(iss["quoted_text"] == line[:110] for iss in issues):
                    roast_text = _select_roast(cat, line, BASELINE_JOKE_BANKS[cat][0])
                    issues.append({
                        "quoted_text": line[:110],
                        "category": cat,
                        "roast": roast_text,
                        "fix": fix_txt,
                    })
                break

    # Numberless bullet check
    if len(issues) < 4:
        for line in lines:
            if not any(char.isdigit() for char in line) and len(line) > 35 and len(issues) < 6:
                if not any(iss["quoted_text"] == line[:110] for iss in issues):
                    roast_text = _select_roast("no-metrics", line, BASELINE_JOKE_BANKS["no-metrics"][0])
                    issues.append({
                        "quoted_text": line[:110],
                        "category": "no-metrics",
                        "roast": roast_text,
                        "fix": "Quantify karo: 'Scaled server throughput by 35% handling 50,000+ requests/min.'",
                    })

    # Typos check in skills or text
    for line in lines:
        lower = line.lower()
        if any(mis in lower for mis in ["skils", "pythno", "javascrip", "mangment", "experiance"]):
            roast_text = _select_roast("typo", line, BASELINE_JOKE_BANKS["typo"][0])
            issues.append({
                "quoted_text": line[:100],
                "category": "typo",
                "roast": roast_text,
                "fix": "Typo fix karo aur submission se pehle spellcheck zaroor run karo.",
            })
            break

    if not issues:
        sample_line = lines[0] if lines else "Experienced Software Developer"
        roast_text = _select_roast("buzzword", sample_line, BASELINE_JOKE_BANKS["buzzword"][0])
        issues.append({
            "quoted_text": sample_line[:100],
            "category": "buzzword",
            "roast": roast_text,
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


# Spelled-out numbers to catch (covers most realistic resume contexts)
_SPELLED_NUMBERS = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|"
    r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\b",
    re.IGNORECASE,
)


def _validate_no_metrics_categorization(data: dict) -> None:
    """
    Server-side safety net: if the AI assigned 'no-metrics' to a line that already
    contains a digit, percentage, or spelled-out number, the categorization is wrong.
    Drop that issue rather than surface a false critique to the user.
    """
    issues = data.get("issues", [])
    clean: list[dict] = []
    for iss in issues:
        if iss.get("category") != "no-metrics":
            clean.append(iss)
            continue
        q = iss.get("quoted_text", "")
        has_digit = bool(re.search(r"\d", q))
        has_pct = "%" in q
        has_spelled = bool(_SPELLED_NUMBERS.search(q))
        if has_digit or has_pct or has_spelled:
            safe_q = q.encode("ascii", "replace").decode("ascii")
            print(
                f"[GUARD] Dropping false 'no-metrics' — quoted_text already contains a number: {safe_q!r:.80}"
            )
        else:
            clean.append(iss)
    data["issues"] = clean


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


def _find_duplicate_roasts(issues: list[dict], threshold: float = 0.70) -> list[tuple[int, str, str]]:
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
    If duplicates remain after retry, substitutes the duplicate with varied Hinglish phrasing
    from the category's expanded joke pool, ensuring no duplicate within the response.
    """
    import difflib

    issues = data.get("issues", [])
    if len(issues) <= 1:
        return

    seen_norms: list[tuple[str, int]] = []

    for idx, iss in enumerate(issues):
        roast = iss.get("roast", "")
        norm = re.sub(r"[^a-z0-9]", "", roast.lower())
        if not norm:
            continue

        is_dup = False
        for prev_norm, _ in seen_norms:
            ratio = difflib.SequenceMatcher(None, norm, prev_norm).ratio()
            if ratio >= 0.70:
                is_dup = True
                break

        if is_dup:
            cat = iss.get("category", "other")
            pool = BASELINE_JOKE_BANKS.get(cat, BASELINE_JOKE_BANKS["other"])

            alt = None
            for candidate in pool:
                cand_norm = re.sub(r"[^a-z0-9]", "", candidate.lower())
                if not any(difflib.SequenceMatcher(None, cand_norm, p_norm).ratio() >= 0.85 for p_norm, _ in seen_norms):
                    alt = candidate
                    break

            if not alt:
                alt = pool[idx % len(pool)]

            safe_orig = roast.encode("ascii", "replace").decode("ascii")
            safe_alt = alt.encode("ascii", "replace").decode("ascii")
            print(f"[INFO] Server-side duplicate roast detected & replaced for issue #{idx+1} ({cat}): {safe_orig!r} -> {safe_alt!r}")
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
    Dynamically injects recent exclusions from anti-repeat memory (Section 1.3)
    and pushes newly generated roast strings into rolling memory.
    """
    if not resume_text or len(resume_text.strip()) < 80:
        raise ValueError("That doesn't look like a full resume — upload the whole document.")

    env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    load_dotenv(dotenv_path=os.path.abspath(env_path), override=True)

    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    # Dynamic exclusion sampling from anti-repeat memory (Section 1.3)
    exclusion_block = anti_repeat_memory.build_exclusion_prompt()

    data: dict | None = None

    # 1. Try Google Gemini
    if gemini_key:
        try:
            data = _call_gemini_api(gemini_key, resume_text, exclusion_block)
            _validate_schema(data, resume_text)
            _validate_no_metrics_categorization(data)
        except Exception as e:
            print(f"[WARN] Gemini API error: {e}")
            data = None

    # 2. Try Groq
    if not data and groq_key:
        try:
            data = _call_groq_api(groq_key, resume_text, exclusion_block)
            _validate_schema(data, resume_text)
            _validate_no_metrics_categorization(data)
        except Exception as e:
            print(f"[WARN] Groq API error: {e}")
            data = None

    # 3. Try Anthropic Claude
    if not data and anthropic_key:
        try:
            data = _call_anthropic_api(anthropic_key, resume_text, exclusion_block)
            _validate_schema(data, resume_text)
            _validate_no_metrics_categorization(data)
        except Exception as e:
            print(f"[WARN] Anthropic API error: {e}")
            data = None

    # 4. Fallback if external API calls fail
    if not data:
        data = _generate_fallback_roast(resume_text, exclusion_block)
        _validate_no_metrics_categorization(data)

    # Server-side anti-repetition / duplicate check safety net (Section 3.7)
    _deduplicate_roasts(data)

    # Push newly generated roasts into category rolling cache
    anti_repeat_memory.record_roasts(data.get("issues", []))

    # Map offsets safely
    quoted_texts = [iss["quoted_text"] for iss in data["issues"]]
    offsets = map_quoted_text_to_offsets(quoted_texts, resume_text)

    for i, issue in enumerate(data["issues"]):
        issue["start_offset"], issue["end_offset"] = offsets[i]
        issue["severity_rank"] = i + 1

    return data
