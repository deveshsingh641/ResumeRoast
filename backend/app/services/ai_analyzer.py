"""
AI analysis service — Hinglish WhatsApp-style Persona
Roasts resumes with savage yet constructive Indian friend energy in natural Hinglish Roman script.
Supports Google Gemini, Groq, Anthropic Claude, and smart fallback engine.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from typing import Any

from dotenv import load_dotenv
import httpx

logger = logging.getLogger(__name__)

from app.services.extractor import map_quoted_text_to_offsets
from app.services.anti_repeat_service import anti_repeat_memory, BASELINE_JOKE_BANKS
from app.i18n.mapping import DEFAULT_LANGUAGE, HINGLISH_LANGUAGE, normalize_language
from app.prompts import get_system_prompt, get_user_prompt_template
from app.prompts.joke_banks import get_joke_banks

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

DYNAMIC BADGE LABELS:
For every issue, also generate a "badge_label" — a short, punchy Hinglish tag (2-4 words, ALL CAPS, no punctuation) that captures what's wrong with this specific line, in the same voice as your roast lines. This label must vary across issues just like your roast text does — never default to the same badge_label every time a category repeats.

Inspiration pool by category (draw from these, vary them, don't treat as a fixed script):

no-metrics: NUMBER KAHAN HAI · PROOF DE DO · DATA GHAYAB HAI · GINTI KAHAN HAI · SABOOT CHAHIYE · IMPACT DIKHAO · KITNA KIYA BHAI

buzzword: BUZZWORD OVERDOSE · GHISA-PITA HAI YE · SUNA-SUNA LAGTA HAI · COPY-PASTE VIBES · GENERIC ALERT · YE SABKA RESUME HAI

formatting: FORMAT BIGDA HUA · LOOK MEIN GADBAD · SPACING ISSUE HAI · ALIGNMENT OFF HAI

length: LAMBA BAHUT KAR DIYA · ITNA LAMBA KYUN · SHORT KARO ZARA

irrelevant: YE KYUN LIKHA BHAI · ISKA YAHAN KAAM NAHI · OUT OF PLACE HAI

typo: SPELLING MISS HAI · GALTI PAKDI GAYI · PROOFREAD NAHI KIYA KYA

other: KUCH GADBAD HAI · YE CLEAR NAHI HAI

The badge_label must still semantically match its category (a no-metrics issue's label should be about missing data/proof, not about formatting) — vary the wording, not the meaning.

OUTPUT SCHEMA (return exactly this JSON structure):
{
  "overall_score": <integer 0-100>,
  "band": <"weak" | "mid" | "strong">,
  "one_line_verdict": "<string, under 12 words — catchy Hinglish roast headline with 1 emoji>",
  "issues": [
    {
      "quoted_text": "<exact substring from the resume in original text>",
      "category": <"buzzword" | "no-metrics" | "formatting" | "length" | "irrelevant" | "typo" | "other">,
      "badge_label": "<short punchy 2-4 words ALL CAPS Hinglish tag, e.g. PROOF DE DO>",
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
      "badge_label": "DATA GHAYAB HAI",
      "roast": "\"Responsible for\" likhna band karo yaar 😩 recruiter ko number chahiye, kahani nahi.",
      "fix": "Kuch is tarah likho: \"Built 12 reusable UI components, cutting page load time by 30%\" — number daalo, impact dikhao."
    },
    {
      "quoted_text": "Worked closely with the design team",
      "category": "buzzword",
      "badge_label": "GENERIC ALERT",
      "roast": "\"Worked closely with\" — matlab kya kiya bhai? Chai piya ya kuch banaya bhi ☕😂",
      "fix": "Specific batao: \"Collaborated with 3 designers to ship the checkout redesign, reducing drop-off by 18%.\""
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
      "badge_label": "SPELLING MISS HAI",
      "roast": "Arre yaar 'Pythno' aur 'Jacascript'? 🤡 Itna jaldi mein the kya ki spellcheck bhi skip kar diya?",
      "fix": "Typo fix karo: 'Python, JavaScript, C++' — submission se pehle ek baar Grammarly ya spellcheck zaroor chalao."
    },
    {
      "quoted_text": "Curriculum Vitae (Page 1 of 4)",
      "category": "length",
      "badge_label": "ITNA LAMBA KYUN",
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
      "badge_label": "OUT OF PLACE HAI",
      "roast": "Bhai biodata thodi hai 😅 ye hobbies likh ke valuable space kyu waste kar rahe ho?",
      "fix": "Hobbies section hatao aur wahan koi relevant project, hackathon rank ya open-source contribution mention karo."
    },
    {
      "quoted_text": "Utilized cutting-edge synergistic paradigms across teams",
      "category": "buzzword",
      "badge_label": "BUZZWORD OVERDOSE",
      "roast": "Itna bhari corporate jargon padh ke recruiter behosh ho jayega bhai 😵 simple bolo!",
      "fix": "Seedha likho: \"Led integration of payment gateway across 4 microservices with 99.9% uptime.\""
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
      "badge_label": "PROOF DE DO",
      "roast": "Pheeka lag raha hai bhai 🥱 'Helped team' se credit nahi milta, exact metric batao.",
      "fix": "Rewrite karo: \"Optimized Redis cache queries, reducing p99 latency from 450ms to 85ms across 12 services.\""
    },
    {
      "quoted_text": "DECLARATION: I hereby declare all information is true to my knowledge",
      "category": "formatting",
      "badge_label": "FORMAT BIGDA HUA",
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

# Dynamic Badge Label Pools (Section 3.8)
BADGE_LABEL_POOLS: dict[str, list[str]] = {
    "no-metrics": [
        "NUMBER KAHAN HAI", "PROOF DE DO", "DATA GHAYAB HAI",
        "GINTI KAHAN HAI", "SABOOT CHAHIYE", "IMPACT DIKHAO", "KITNA KIYA BHAI"
    ],
    "buzzword": [
        "BUZZWORD OVERDOSE", "GHISA-PITA HAI YE", "SUNA-SUNA LAGTA HAI",
        "COPY-PASTE VIBES", "GENERIC ALERT", "YE SABKA RESUME HAI"
    ],
    "formatting": [
        "FORMAT BIGDA HUA", "LOOK MEIN GADBAD", "SPACING ISSUE HAI", "ALIGNMENT OFF HAI"
    ],
    "length": [
        "LAMBA BAHUT KAR DIYA", "ITNA LAMBA KYUN", "SHORT KARO ZARA"
    ],
    "irrelevant": [
        "YE KYUN LIKHA BHAI", "ISKA YAHAN KAAM NAHI", "OUT OF PLACE HAI"
    ],
    "typo": [
        "SPELLING MISS HAI", "GALTI PAKDI GAYI", "PROOFREAD NAHI KIYA KYA"
    ],
    "other": [
        "KUCH GADBAD HAI", "YE CLEAR NAHI HAI"
    ]
}

ENGLISH_BADGE_LABEL_POOLS: dict[str, list[str]] = {
    "no-metrics": [
        "WHERE IS PROOF", "NUMBERS MISSING", "ZERO DATA",
        "QUANTIFY THIS", "SHOW METRICS", "WHERE IS IMPACT"
    ],
    "buzzword": [
        "BUZZWORD OVERLOAD", "PURE JARGON", "COPY-PASTE VIBES",
        "GENERIC ALERT", "EMPTY BUZZWORDS"
    ],
    "formatting": [
        "FORMATTING CHAOS", "LOOKS MESSY", "SPACING ISSUE", "ALIGNMENT OFF"
    ],
    "length": [
        "TRIM THE FAT", "TOO LONG", "CUT TO CHASE", "CONDENSE THIS"
    ],
    "irrelevant": [
        "OUT OF PLACE", "WHY IS THIS HERE", "UNRELATED DETAIL"
    ],
    "typo": [
        "SPELLCHECK FAILED", "TYPO DETECTED", "PROOFREAD ERROR"
    ],
    "other": [
        "NEEDS CLARITY", "UNCLEAR STATEMENT"
    ]
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

def _call_gemini_api(api_key: str, resume_text: str, exclusion_block: str = "", language: str = DEFAULT_LANGUAGE) -> dict:
    sys_prompt = get_system_prompt(language)
    user_template = get_user_prompt_template(language)
    formatted_user_prompt = user_template.format(
        resume_text=resume_text[:12000],
        exclusion_block=f"\n{exclusion_block}\n" if exclusion_block else "",
    )
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"{sys_prompt}\n\n{formatted_user_prompt}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.7,
        },
    }

    candidate_models = [os.getenv("GEMINI_MODEL", "gemini-3.6-flash"), "gemini-flash-latest"]
    last_err = None
    with httpx.Client(timeout=45.0) as client:
        for model in candidate_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            try:
                response = client.post(url, json=payload)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                data = response.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                return _extract_json(raw_text)
            except Exception as e:
                last_err = e
        if last_err:
            raise last_err
    return {}


# ---------------------------------------------------------------------------
# Provider 2: Groq (Free API Key from https://console.groq.com)
# ---------------------------------------------------------------------------

def _call_groq_api(api_key: str, resume_text: str, exclusion_block: str = "", language: str = DEFAULT_LANGUAGE) -> dict:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    sys_prompt = get_system_prompt(language)
    user_template = get_user_prompt_template(language)
    formatted_user_prompt = user_template.format(
        resume_text=resume_text[:12000],
        exclusion_block=f"\n{exclusion_block}\n" if exclusion_block else "",
    )
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": sys_prompt},
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

def _call_anthropic_api(api_key: str, resume_text: str, exclusion_block: str = "", language: str = DEFAULT_LANGUAGE) -> dict:
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key, timeout=45.0)
    sys_prompt = get_system_prompt(language)
    user_template = get_user_prompt_template(language)
    formatted_user_prompt = user_template.format(
        resume_text=resume_text[:12000],
        exclusion_block=f"\n{exclusion_block}\n" if exclusion_block else "",
    )
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        system=sys_prompt,
        messages=[{"role": "user", "content": formatted_user_prompt}],
        temperature=0.7,
    )
    raw_text = response.content[0].text
    return _extract_json(raw_text)


# ---------------------------------------------------------------------------
# Fallback Roast Generator in Authentic Hinglish
# ---------------------------------------------------------------------------
# Heuristic Scoring & Fallback Roast Generator (Deep Grounded Engine)
# ---------------------------------------------------------------------------

DOMAIN_KEYWORDS = {
    "healthcare": ["patient", "clinical", "nurse", "hospital", "triage", "surgery", "medical", "doctor", "physician", "health", "care", "diagnosis", "therapy"],
    "finance": ["financial", "portfolio", "equity", "dcf", "valuation", "budget", "accounting", "ledger", "revenue", "audit", "banking", "capital", "sec", "earnings"],
    "engineering": ["software", "engineer", "developer", "api", "react", "python", "kubernetes", "docker", "cloud", "aws", "database", "backend", "frontend", "devops", "code", "system"],
    "culinary": ["chef", "kitchen", "culinary", "restaurant", "menu", "cook", "food", "haccp", "dining", "brigade", "recipes"],
    "legal": ["attorney", "counsel", "litigation", "contract", "compliance", "law", "legal", "statute", "court", "regulatory", "due diligence"],
    "education": ["teacher", "student", "curriculum", "school", "teaching", "education", "classroom", "physics", "academic", "course", "lecture"],
    "marketing": ["marketing", "seo", "campaign", "ads", "growth", "social media", "conversion", "funnel", "brand", "content", "traffic"],
    "design": ["figma", "designer", "ux", "ui", "wireframe", "prototype", "design system", "typography", "usability", "visual"],
}

VERDICT_POOLS = {
    "hi-IN": {
        "weak_metrics": [
            "Bhai resume mein sirf baatein hain, proof kahan hai? Data missing hai 📊",
            "Number daalna bhool gaye kya bhai? Recruiter suspense movie nahi dekhega 📉",
            "Sab theek hai boss, par calculator leke baithna padega impact samajhne ke liye 🧮",
            "Kahani achhi likhi hai yaar, par numbers bina recruiter aage scroll kar dega 🥱",
            "Bina numbers ke ye claim hawa-hawaai lag raha hai, data daalo boss 💨",
        ],
        "weak_buzzwords": [
            "Bhai resume hai ya buzzword dictionary? Thoda asli kaam batao 🤖",
            "Itna corporate jargon bhar diya, recruiter ko oxygen mask lagega 😵",
            "LinkedIn influencers ki tarah bolna band karo, seedha point pe aao 😅",
            "Ye word har doosre resume mein hai bhai, tu unique kaise banega isse? 🎭",
            "Adjectives bohot hain boss, par delivery proof ek bhi nahi dikh raha 🛑",
        ],
        "weak_general": [
            "Bhai resume hai ya suspense novel? 🕵️",
            "Design aur content dekh ke lag raha hai jaldi mein submit kiya tha 😭",
            "Ekdum generic lag raha hai bhai, thoda effort aur specific details chahiye 📄",
        ],
        "mid_metrics": [
            "Dum hai boss, bas thoda masala aur metrics kam hain 🍛",
            "Base solid hai bhai, bas impact ko bold mein numbers ke saath dikhao 🚀",
            "Acha effort hai yaar, par key bullets mein quantifiable metrics missing hain 📊",
        ],
        "mid_buzzwords": [
            "Acha effort hai yaar, par buzzwords zyada bhar diye hain 🤖",
            "Kaam solid dikh raha hai boss, par corporate jargon thoda trim karo ✂️",
            "Profile mein dum hai, bas thodi generic lines delete karke punchy banao 💥",
        ],
        "mid_general": [
            "Thodi polishing baaki hai boss, shortlist ke kaafi kareeb ho ✨",
            "Section structure clean hai, bas bullet points ko impact-first banao 🎯",
            "Acha profile hai, bas 2-3 killer numbers daal do toh recruiter mana nahi karega 📈",
        ],
        "strong": [
            "Arey waah! Solid resume banaya hai, bas minor polishing ki zaroorat hai 🔥",
            "Recruiter shortlist zaroor karega, bas 1-2 sharp tweaks kardo 🎯",
            "Bohot badhiya draft hai boss — strong impact aur clear structure 🚀",
            "Shaandaar profile hai, bas formatting ko 100% airtight rakhna 👍",
        ],
    },
    "en": {
        "weak_metrics": [
            "Solid narrative, but your metrics went completely missing in action 📉",
            "Where is the proof? Claims without numbers read like wishful thinking 📊",
            "Recruiters give this six seconds — give them hard numbers to look at ⏱️",
            "Lots of responsibilities listed, zero measurable outcomes delivered 🧮",
            "Is this a resume or a mystery novel? Let's see some evidence 🕵️",
        ],
        "weak_buzzwords": [
            "Drowned in corporate buzzwords — what did you actually ship? 🤖",
            "Too much corporate fluff, not enough concrete business impact 😵",
            "A dictionary of clichés that tells recruiters almost nothing 📄",
            "Every second resume uses these exact phrases — stand out with facts 🎭",
            "Heavy on corporate adjectives, light on actual verified accomplishments 🛑",
        ],
        "weak_general": [
            "Visually cramped — give your achievements room to breathe 📄",
            "Reads like a generic job description rather than a personal track record 📑",
            "The foundation is unpolished — tighten the structure and prune the filler ✂️",
        ],
        "mid_metrics": [
            "Solid technical foundation, but your metrics went missing in action 📉",
            "Strong domain experience hiding behind vague responsibility statements 🎯",
            "Good track record — just back up your top 3 claims with hard numbers 📊",
        ],
        "mid_buzzwords": [
            "Good effort, but drowned in corporate buzzwords and vague claims 🤖",
            "Good background — swap generic buzzwords for specific tools and outcomes 💡",
            "Solid experience that gets diluted by overused corporate phrases ✂️",
        ],
        "mid_general": [
            "Clean structure and clear direction — just needs sharper impact metrics 🚀",
            "Promising candidate profile — tighten the phrasing and highlight key wins 🎯",
            "Solid baseline — a few quantitative tweaks will make this shortlist-ready 📈",
        ],
        "strong": [
            "Sharp, impactful, and clear — just needs minor edge polishing 🔥",
            "Strong candidate profile with measurable accomplishments on display 🚀",
            "Standout resume with clear impact, strong hierarchy, and credible metrics 📈",
            "Impressive trajectory — minor phrasing tweaks will make this elite 🎯",
        ],
    },
}


def _detect_domain(text: str) -> str:
    lower = text.lower()
    scores: dict[str, int] = {}
    for domain, kws in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in kws if re.search(rf"\b{re.escape(kw)}\b", lower))
        scores[domain] = score
    best = max(scores, key=scores.get)
    return best if scores[best] >= 2 else "general"


def _generate_domain_fix(line: str, domain: str, cat: str, lang: str) -> str:
    if cat == "no-metrics":
        if domain == "healthcare":
            return (
                "Quantify karo: 'Triage kiya 25+ emergency patients per shift with zero protocol deviations'."
                if lang == "hi-IN"
                else "Quantify this: 'Triaged 25+ emergency patients per shift with zero protocol deviations'."
            )
        elif domain == "finance":
            return (
                "Number daalo: 'Modeled DCF valuations for 15+ tech equities managing $40M portfolio'."
                if lang == "hi-IN"
                else "Quantify this: 'Modeled DCF valuations for 15+ tech equities managing $40M portfolio'."
            )
        elif domain == "culinary":
            return (
                "Metric daalo: 'Supervised kitchen brigade of 14 cooks, cutting food cost percentage by 4.5%'."
                if lang == "hi-IN"
                else "Quantify this: 'Supervised kitchen brigade of 14 cooks, cutting food cost percentage by 4.5%'."
            )
        elif domain == "legal":
            return (
                "Exact count daalo: 'Negotiated 45+ enterprise SaaS agreements totaling $12M in ARR'."
                if lang == "hi-IN"
                else "Quantify this: 'Negotiated 45+ enterprise SaaS agreements totaling $12M in ARR'."
            )
        elif domain == "education":
            return (
                "Impact metric dikhao: 'Instructed 95+ students achieving an 88% AP pass rate'."
                if lang == "hi-IN"
                else "Quantify this: 'Instructed 95+ students achieving an 88% AP pass rate'."
            )
        elif domain == "marketing":
            return (
                "Performance number daalo: 'Optimized Google Ads CPA by 28%, driving 1,400+ qualified MQLs'."
                if lang == "hi-IN"
                else "Quantify this: 'Optimized Google Ads CPA by 28%, driving 1,400+ qualified MQLs'."
            )
        elif domain == "design":
            return (
                "Metric add karo: 'Designed mobile checkout flow tested with 30 users, reducing drop-off by 18%'."
                if lang == "hi-IN"
                else "Quantify this: 'Designed mobile checkout flow tested with 30 users, reducing drop-off by 18%'."
            )
        elif domain == "engineering":
            return (
                "Production scale likho: 'Architected microservice handling 45,000 req/min with 99.9% uptime'."
                if lang == "hi-IN"
                else "Quantify this: 'Architected microservice handling 45,000 req/min with 99.9% uptime'."
            )
        else:
            return (
                "Quantify karo: Action verb + exact number/percent + business outcome daalo."
                if lang == "hi-IN"
                else "Quantify this: Start with an active verb, insert concrete numbers/percentages, and end with the outcome."
            )
    elif cat == "buzzword":
        return (
            "Buzzword hatao aur direct bolo: Kaunsa tool use kiya aur uska tangible result kya tha."
            if lang == "hi-IN"
            else "Drop the corporate jargon and state the concrete tool used and the resulting business outcome."
        )
    elif cat == "length":
        return (
            "Header aur summary choti karo; purani schooling hata ke whitespace bachaao."
            if lang == "hi-IN"
            else "Trim summary and older schooling to ensure high-impact recent accomplishments stand out."
        )
    elif cat == "irrelevant":
        return (
            "Ye line delete karo aur wahan verifiable project links ya certifications mention karo."
            if lang == "hi-IN"
            else "Delete this line and replace the space with verified technical projects or certifications."
        )
    elif cat == "typo":
        return (
            "Typo correct karo aur submission se pehle automated spellcheck zaroor chalao."
            if lang == "hi-IN"
            else "Correct typo and run an automated spellchecker before submitting your application."
        )
    return (
        "Rephrase with strong action verbs and specific facts."
        if lang != "hi-IN"
        else "Strong action verb aur specific facts ke saath rewrite karo."
    )


KNOWN_TOOLS = [
    "react", "python", "javascript", "typescript", "api", "graphql", "aws", "gcp",
    "docker", "kubernetes", "postgres", "sql", "redis", "kafka", "spark", "flutter",
    "swift", "cypress", "selenium", "node", "java", "c++", "go", "ci/cd", "etl",
    "linux", "cloud", "ui", "database", "backend", "frontend", "devops",
    "figma", "revit", "etabs", "dcf", "epic", "haccp", "splunk", "oscp"
]


def _extract_tool(text: str) -> str | None:
    t_lower = text.lower()
    for t in KNOWN_TOOLS:
        if re.search(rf"\b{re.escape(t)}\b", t_lower):
            return t
    return None


def _calculate_grounded_score(
    resume_text: str, lines: list[str], issues: list[dict], domain: str
) -> int:
    """
    Computes a realistic, nuanced 0-100 score based on actual document characteristics:
    - Metric density (continuous response curve)
    - Action verb strength
    - Buzzword and cliché count
    - Length and depth balance
    - Section presence
    - Lexical diversity & vocabulary richness
    - Fine-grained deterministic tie-breaker based on document content hash
    """
    raw_lower = resume_text.lower()
    total_lines = max(1, len(lines))

    # 1. Base Score
    score = 52.0

    # 2. Metric density evaluation (continuous curve)
    metric_lines = sum(
        1 for line in lines
        if any(c.isdigit() for c in line) or "%" in line or "$" in line or "₹" in line
        or bool(_SPELLED_NUMBERS.search(line))
    )
    metric_ratio = metric_lines / total_lines
    score += max(-14.0, min(22.0, (metric_ratio * 40.0) - 10.0))

    # 3. Strong Action Verbs vs Passive Verbs
    strong_verbs = [
        "led", "built", "architected", "spearheaded", "designed", "developed", "optimized",
        "managed", "negotiated", "audited", "triaged", "directed", "executed", "conducted",
        "authored", "engineered", "orchestrated", "automated", "streamlined", "formulated"
    ]
    weak_verbs = ["responsible for", "assisted", "helped", "worked on", "duties included", "participated in"]

    strong_count = sum(1 for v in strong_verbs if re.search(rf"\b{re.escape(v)}\b", raw_lower))
    weak_count = sum(1 for v in weak_verbs if v in raw_lower)

    score += min(14.0, strong_count * 2.5)
    score -= min(12.0, weak_count * 3.0)

    # 4. Buzzword & Cliché penalties
    buzzword_penalties = sum(1 for iss in issues if iss.get("category") == "buzzword")
    score -= min(14.0, buzzword_penalties * 3.5)

    # 5. Length & Substance balance
    word_count = len(resume_text.split())
    if word_count < 140:
        score -= 16.0  # Too sparse
    elif word_count < 250:
        score -= 6.0
    elif 300 <= word_count <= 950:
        score += 6.0   # Sweet spot
    elif word_count > 1600:
        score -= 8.0   # Excessive novella

    # 6. Lexical diversity & vocabulary richness
    words = [w for w in raw_lower.split() if len(w) > 2]
    unique_words_count = len(set(words))
    lexical_ratio = unique_words_count / max(1, len(words))
    score += (lexical_ratio - 0.50) * 16.0

    # 7. Structural sections presence
    if any(h in raw_lower for h in ["experience", "employment", "work history", "clinical experience", "engagement history"]):
        score += 4.0
    if any(h in raw_lower for h in ["education", "academic", "degree", "university", "college"]):
        score += 4.0
    if any(h in raw_lower for h in ["skills", "certifications", "technical arsenal", "licens"]):
        score += 4.0

    # 8. Issue severity drag
    score -= min(15.0, len(issues) * 2.0)

    # 9. Deterministic content micro-variance (prevents exact artificial ties across distinct inputs)
    content_hash_full = hashlib.sha256(resume_text.strip().encode("utf-8")).hexdigest()
    h1 = int(content_hash_full[:8], 16)
    h2 = int(content_hash_full[8:16], 16)
    v1 = (h1 % 29) - 14
    v2 = (h2 % 5) - 2
    char_offset = ((len(resume_text) % 13) - 6) * 0.6
    score += v1 + (v2 * 0.5) + char_offset

    # Clamp to valid, realistic range (16 - 88)
    final_score = int(max(16, min(88, round(score))))
    return final_score


def _extract_grounded_strengths(resume_text: str, domain: str, lang: str) -> list[str]:
    """
    Extracts authentic, candidate-specific strengths from the uploaded resume text.
    """
    strengths: list[str] = []
    lower = resume_text.lower()

    # 1. Tech / Domain Tools detection
    found_tools = []
    ALL_TOOLS = [
        "React", "TypeScript", "Python", "Kubernetes", "Docker", "AWS", "Terraform", "PostgreSQL",
        "Redux", "Storybook", "Figma", "ETABS", "Revit", "SAP2000", "DCF", "Bloomberg", "VBA",
        "Epic", "BLS", "ACLS", "HIPAA", "HACCP", "ServSafe", "Google Ads", "HubSpot", "Klaviyo",
        "ArgoCD", "Prometheus", "Grafana", "OSCP", "CISSP", "Splunk", "Linux", "Java", "C++"
    ]
    for tool in ALL_TOOLS:
        if re.search(rf"\b{re.escape(tool.lower())}\b", lower):
            found_tools.append(tool)

    if found_tools:
        tools_sample = ", ".join(found_tools[:3])
        if lang == "hi-IN":
            strengths.append(f"Domain tech stack standout hai — {tools_sample} hands-on expertise clear dikhti hai 🚀")
        else:
            strengths.append(f"Core technical domain is evident — practical expertise in {tools_sample} highlighted 🚀")

    # 2. Measurable Metrics detection
    has_metrics = bool(re.search(r"\b\d+%\b|\$\d+|\b\d+\s*(users|clients|patients|requests|accounts|stocks|million|k)\b", lower))
    if has_metrics:
        if lang == "hi-IN":
            strengths.append("Key accomplishments mein quantifiable numbers aur concrete impact shamil hai 📈")
        else:
            strengths.append("Features quantifiable data points and concrete business metrics in experience entries 📈")

    # 3. Live Links / Verification detection
    has_links = bool(re.search(r"github\.com|linkedin\.com|[a-zA-Z0-9.-]+\.(com|io|net|org|dev)", lower))
    if has_links:
        if lang == "hi-IN":
            strengths.append("Live links aur professional profiles provided hain, recruiter easily verify kar sakta hai 🔗")
        else:
            strengths.append("Public profiles and verification links are present for recruiter cross-referencing 🔗")

    # 4. Credentials & Degrees detection
    has_credentials = bool(re.search(r"\b(ph\.d|m\.s\.|b\.s\.|cfa|pe|dvm|rn|oscp|cissp|j\.d\.|mba)\b", lower))
    if has_credentials:
        if lang == "hi-IN":
            strengths.append("Educational pedigree aur certifications clearly structured hain 🎓")
        else:
            strengths.append("Professional credentials and academic background are prominently structured 🎓")

    # 5. Clean Structure fallback
    if len(strengths) < 2:
        if lang == "hi-IN":
            strengths.append("Section hierarchy clean hai boss, ATS scanners ko padhne mein asani hogi 👍")
        else:
            strengths.append("Clean section hierarchy — ATS scanners and hiring managers can parse this easily 👍")

    return strengths[:2]


def _generate_grounded_verdict(
    resume_text: str,
    domain: str,
    band: str,
    top_cat: str,
    lang: str,
) -> str:
    """
    Produces an authentically grounded, domain- and tool-aware verdict that
    uniquely reflects the specific resume's content, avoiding repetitive generic lines.
    """
    tool = _extract_tool(resume_text)
    t_name = tool.title() if tool else None
    content_hash_num = int(hashlib.sha256(resume_text.strip().encode("utf-8")).hexdigest()[:8], 16)

    if lang == "hi-IN":
        domain_verdicts = {
            "culinary": [
                "Chef ka haath toh dikh raha hai boss, par inventory aur food cost ke numbers gayab hain 🍳",
                "Kitchen leadership solid hai, par cover volume aur daily order count missing hai 🔪",
            ],
            "legal": [
                "Vakalat achhi hai boss, par contracts aur deal sizes ke quantifiable numbers kahan hain? ⚖️",
                "Legal drafting clean hai, par case volume aur transaction scale suspense mein hain 📜",
            ],
            "finance": [
                "Finance background solid hai bhai, par portfolio scale aur DCF metrics gayab hain 📊",
                "Equity research clean hai, par dollar figures aur returns ke exact numbers do 💼",
            ],
            "healthcare": [
                "Clinical care solid hai, par patient volume aur ER protocol metrics daalna zaroori hai 🩺",
                "Patient care standout hai boss, par triage volume aur treatment metrics add karo 🏥",
            ],
            "education": [
                "Padhai solid karwayi hai, par student pass percentages aur test scores ka proof do 🍎",
                "Teaching dedication clear hai, par class sizes aur performance gains quantify karo 📚",
            ],
            "marketing": [
                "Campaigns ache hain boss, par CAC, ROAS aur lead conversion numbers kahan hain? 📣",
                "Marketing copy creative hai, par CTR aur qualified leads ka data gayab hai 📈",
            ],
            "design": [
                "Design portfolio clean hai, par user retention aur checkout drop-off numbers kahan gaye? 🎨",
                "Figma screens sundar hain, par usability testing aur conversion gains quantify karo 🖌️",
            ],
            "engineering": [
                f"'{t_name}' stack toh solid use kiya hai bhai, par production scale aur metrics gayab hain 📉" if t_name else "Engineering experience solid hai, par system throughput aur scale metrics gayab hain 💻",
                f"'{t_name}' pe kaam kiya achha hai boss, par latency aur user numbers quantify karo 🚀" if t_name else "Clean technical foundation, par latency aur reliability ke numbers missing hain ⚙️",
            ],
        }
        tool_options = [
            f"'{t_name}' stack toh use kiya hai bhai, par production scale aur metrics missing hain 📉",
            f"'{t_name}' pe kaam kiya sahi hai boss, par impact numbers aur scale quantify karo 🚀",
            f"'{t_name}' ka experience dikhta hai, par buzzwords chhodke exact metrics do 🎯",
        ] if t_name else []
    else:
        domain_verdicts = {
            "culinary": [
                "Culinary experience is clear, but recipes don't convince hiring managers without food cost numbers 🍳",
                "Kitchen leadership is evident, but inventory savings and cover volume went missing 🔪",
            ],
            "legal": [
                "Legal background is evident, but contract values and transaction volumes are omitted ⚖️",
                "Strong contract drafting, but silent on deal sizes and litigation outcome metrics 📜",
            ],
            "finance": [
                "Financial modeling background is clear, but portfolio sizes and DCF variance went missing 📊",
                "Solid analytical foundation, but needs concrete dollar figures and investment returns 💼",
            ],
            "healthcare": [
                "Clinical nursing care is evident, but patient ratios and triage volumes are missing 🩺",
                "Dedicated patient care on display, but needs measurable clinical volume and outcomes 🏥",
            ],
            "education": [
                "Teaching dedication is clear, but student outcome percentiles and pass metrics need numbers 🍎",
                "Strong classroom instruction, but silent on standardized score gains and class sizes 📚",
            ],
            "marketing": [
                "Campaign strategy is visible, but CAC, ROAS, and pipeline conversion numbers went missing 📣",
                "Creative marketing vision, but where are the MQL growth figures and campaign metrics? 📈",
            ],
            "design": [
                "Visual design sense is clear, but conversion impact and user retention metrics went missing 🎨",
                "Thoughtful UX workflows, but needs hard metrics on user drop-off reduction and adoption 🖌️",
            ],
            "engineering": [
                f"Solid technical arsenal with '{t_name}', but production throughput and scale numbers went missing 📉" if t_name else "Engineering experience is visible, but system throughput and scale metrics went missing 💻",
                f"Hands-on expertise with '{t_name}', but needs quantifiable uptime and latency metrics 🚀" if t_name else "Clean technical foundation, but lacks concrete latency and reliability metrics ⚙️",
            ],
        }
        tool_options = [
            f"Solid technical arsenal with '{t_name}', but production throughput and scale numbers went missing 📉",
            f"Hands-on expertise with '{t_name}', but needs quantifiable uptime and latency metrics 🚀",
            f"Demonstrated proficiency in '{t_name}', but pair it with measurable impact rather than buzzwords 🎯",
        ] if t_name else []

    if tool_options and domain in ("engineering", "general"):
        return tool_options[content_hash_num % len(tool_options)]

    if domain in domain_verdicts:
        pool = domain_verdicts[domain]
        return pool[content_hash_num % len(pool)]

    lang_pool = VERDICT_POOLS.get(lang, VERDICT_POOLS["en"])
    if band == "strong":
        candidates = lang_pool.get("strong", [])
    elif band == "mid":
        if top_cat == "no-metrics":
            candidates = lang_pool.get("mid_metrics", lang_pool["mid_general"])
        elif top_cat == "buzzword":
            candidates = lang_pool.get("mid_buzzwords", lang_pool["mid_general"])
        else:
            candidates = lang_pool.get("mid_general", [])
    else:
        if top_cat == "no-metrics":
            candidates = lang_pool.get("weak_metrics", lang_pool["weak_general"])
        elif top_cat == "buzzword":
            candidates = lang_pool.get("weak_buzzwords", lang_pool["weak_general"])
        else:
            candidates = lang_pool.get("weak_general", [])

    return candidates[content_hash_num % len(candidates)] if candidates else "Resume needs focused improvements."


def _generate_fallback_roast(
    resume_text: str, exclusion_block: str = "", language: str = HINGLISH_LANGUAGE
) -> dict[str, Any]:
    """
    Intelligent heuristic fallback analyzer with language-specific persona.
    Quotes actual candidate lines and generates shareable roasts from vocabulary pool,
    actively avoiding recently used lines.
    Calculates dynamic scores, varied verdicts, and context-aware fixes.
    """
    import random
    lang = normalize_language(language)
    joke_bank = get_joke_banks(lang)
    domain = _detect_domain(resume_text)

    lines = [
        line.strip() for line in resume_text.splitlines()
        if len(line.strip()) > 20 and not line.strip().startswith("http")
    ]

    recent_exclusions = set(anti_repeat_memory.get_recent_roasts())
    used_roasts: set[str] = set()

    def _select_roast(cat: str, line_quote: str, fallback_default: str) -> str:
        tool = _extract_tool(line_quote)
        grounded_options = []

        if tool:
            t_name = tool.title()
            if lang == "hi-IN":
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
            else:
                if cat == "no-metrics":
                    grounded_options = [
                        f"Claimed scale with '{t_name}', but how many users or queries? Give us the numbers.",
                        f"Mentioned '{t_name}' performance gains — was that 2% or 200%? The data went missing 📊",
                        f"Using '{t_name}' is fine, but at what production volume? What scale are we talking? 👀",
                        f"Pair '{t_name}' with an exact measurable outcome — claims without numbers are just vibes 📉",
                    ]
                elif cat == "buzzword":
                    grounded_options = [
                        f"Stuffed corporate buzzwords around '{t_name}'. Now show what actually shipped.",
                        f"Every resume on earth pairs '{t_name}' with this generic phrase. What made your work unique?",
                        f"Good to know you used '{t_name}', but this bullet sounds like it was copied straight from LinkedIn 😅",
                    ]

        pool = list(joke_bank.get(cat, joke_bank.get("other", [fallback_default])))
        combined = grounded_options + pool
        candidates = [r for r in combined if r not in used_roasts and r not in recent_exclusions]
        if not candidates:
            candidates = [r for r in combined if r not in used_roasts]
        chosen = random.choice(candidates) if candidates else fallback_default
        used_roasts.add(chosen)
        return chosen

    used_badges: set[str] = set()
    badge_pool_map = BADGE_LABEL_POOLS if lang == "hi-IN" else ENGLISH_BADGE_LABEL_POOLS

    def _select_badge(cat: str) -> str:
        cat_pool = badge_pool_map.get(cat, badge_pool_map.get("other", ["FLAGGED"]))
        for b in cat_pool:
            if b not in used_badges:
                used_badges.add(b)
                return b
        fallback = cat_pool[len(used_badges) % len(cat_pool)]
        used_badges.add(fallback)
        return fallback

    issues = []
    buzzwords = [
        ("responsible for", "no-metrics"),
        ("worked closely with", "buzzword"),
        ("synerg", "buzzword"),
        ("spearheaded", "buzzword"),
        ("passionate", "buzzword"),
        ("assisted", "no-metrics"),
        ("curriculum vitae", "length"),
        ("declaration", "irrelevant"),
        ("hobbies", "irrelevant"),
        ("go-getter", "buzzword"),
        ("detail-oriented", "buzzword"),
        ("hardworking", "buzzword"),
        ("dynamic environment", "buzzword"),
        ("team player", "buzzword"),
        ("proven track record", "buzzword"),
    ]

    default_cat_joke = joke_bank.get("other", ["Need more details"])[0]

    for line in lines:
        lower = line.lower()
        for bw, cat in buzzwords:
            if bw in lower and len(issues) < 6:
                if not any(iss["quoted_text"] == line[:110] for iss in issues):
                    fallback_text = joke_bank.get(cat, [default_cat_joke])[0]
                    roast_text = _select_roast(cat, line, fallback_text)
                    fix_txt = _generate_domain_fix(line, domain, cat, lang)
                    issues.append({
                        "quoted_text": line[:110],
                        "category": cat,
                        "badge_label": _select_badge(cat),
                        "roast": roast_text,
                        "fix": fix_txt,
                    })
                break

    # Numberless bullet check
    if len(issues) < 4:
        for line in lines:
            if not any(char.isdigit() for char in line) and len(line) > 35 and len(issues) < 6:
                if not any(iss["quoted_text"] == line[:110] for iss in issues):
                    fallback_text = joke_bank.get("no-metrics", [default_cat_joke])[0]
                    roast_text = _select_roast("no-metrics", line, fallback_text)
                    fix_advice = _generate_domain_fix(line, domain, "no-metrics", lang)
                    issues.append({
                        "quoted_text": line[:110],
                        "category": "no-metrics",
                        "badge_label": _select_badge("no-metrics"),
                        "roast": roast_text,
                        "fix": fix_advice,
                    })

    # Typos check in skills or text
    for line in lines:
        lower = line.lower()
        if any(mis in lower for mis in ["skils", "pythno", "javascrip", "mangment", "experiance"]):
            fallback_text = joke_bank.get("typo", [default_cat_joke])[0]
            roast_text = _select_roast("typo", line, fallback_text)
            fix_advice = _generate_domain_fix(line, domain, "typo", lang)
            issues.append({
                "quoted_text": line[:100],
                "category": "typo",
                "badge_label": _select_badge("typo"),
                "roast": roast_text,
                "fix": fix_advice,
            })
            break

    if not issues:
        if lines:
            sample_line = lines[0]
        else:
            non_empty_lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
            sample_line = non_empty_lines[0] if non_empty_lines else resume_text[:60].strip()
        fallback_text = joke_bank.get("buzzword", [default_cat_joke])[0]
        roast_text = _select_roast("buzzword", sample_line, fallback_text)
        fix_advice = _generate_domain_fix(sample_line, domain, "buzzword", lang)
        issues.append({
            "quoted_text": sample_line[:100],
            "category": "buzzword",
            "badge_label": _select_badge("buzzword"),
            "roast": roast_text,
            "fix": fix_advice,
        })

    # Calculate dynamic, grounded score
    score = _calculate_grounded_score(resume_text, lines, issues, domain)
    if score <= 40:
        band = "weak"
    elif score <= 70:
        band = "mid"
    else:
        band = "strong"

    # Select dynamic verdict based on band & dominant weakness
    cat_counts: dict[str, int] = {}
    for iss in issues:
        cat_counts[iss["category"]] = cat_counts.get(iss["category"], 0) + 1
    top_cat = max(cat_counts, key=cat_counts.get) if cat_counts else "general"

    verdict = _generate_grounded_verdict(resume_text, domain, band, top_cat, lang)
    strengths = _extract_grounded_strengths(resume_text, domain, lang)

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


def _validate_schema(data: dict, resume_text: str | None = None, language: str = HINGLISH_LANGUAGE) -> None:
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

    lang = normalize_language(language)
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

        # Dynamic badge label validation (Section 3.8)
        badge = str(issue.get("badge_label", "")).strip().upper()
        clean_badge = re.sub(r"[^A-Z0-9\s]", "", badge).strip()
        if not clean_badge:
            pool = BADGE_LABEL_POOLS.get(cat, BADGE_LABEL_POOLS["other"]) if lang == "hi-IN" else ENGLISH_BADGE_LABEL_POOLS.get(cat, ENGLISH_BADGE_LABEL_POOLS["other"])
            clean_badge = pool[0]
        issue["badge_label"] = clean_badge

        validated_issues.append(issue)

    if not validated_issues:
        raise ValueError("No valid grounded issues found in analysis")

    # Tone guard: language-aware
    if lang == "hi-IN":
        if hinglish_roast_count == 0 and not _has_hinglish_tone(verdict):
            raise ValueError("AI response failed Hinglish tone check — missing conversational Hinglish markers")
    else:
        if not verdict or len(verdict.strip()) < 5:
            raise ValueError("AI response failed English quality check — verdict too short")

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


def _deduplicate_roasts(data: dict, language: str = HINGLISH_LANGUAGE) -> None:
    """
    Lightweight server-side safety net (Section 3.7 & 3.8).
    Compares all roast strings pairwise using normalized string similarity (>85%).
    If duplicates remain after retry, substitutes the duplicate with varied phrasing
    from the category's expanded joke pool, ensuring no duplicate within the response.
    Also deduplicates dynamic badge labels so no two issues share the exact same badge tag.
    """
    import difflib

    issues = data.get("issues", [])
    if len(issues) <= 1:
        return

    lang = normalize_language(language)
    joke_bank = get_joke_banks(lang)
    badge_pool_map = BADGE_LABEL_POOLS if lang == "hi-IN" else ENGLISH_BADGE_LABEL_POOLS

    seen_norms: list[tuple[str, int]] = []

    # 1. Deduplicate roast text
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
            pool = joke_bank.get(cat, joke_bank.get("other", ["Need more details"]))

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

    # 2. Deduplicate badge labels (Section 3.8)
    seen_badges: set[str] = set()
    for idx, iss in enumerate(issues):
        cat = iss.get("category", "other")
        badge = str(iss.get("badge_label", "")).strip().upper()
        clean_b = re.sub(r"[^A-Z0-9\s]", "", badge).strip()
        cat_pool = badge_pool_map.get(cat, badge_pool_map.get("other", ["FLAGGED"]))

        if not clean_b or clean_b in seen_badges:
            alt_badge = None
            for cand in cat_pool:
                if cand not in seen_badges:
                    alt_badge = cand
                    break
            if not alt_badge:
                alt_badge = cat_pool[idx % len(cat_pool)]
            iss["badge_label"] = alt_badge
            clean_b = alt_badge

        seen_badges.add(clean_b)


# ---------------------------------------------------------------------------
# Main Router
# ---------------------------------------------------------------------------

def analyze_resume(resume_text: str, language: str = DEFAULT_LANGUAGE) -> dict[str, Any]:
    """
    Analyzes resume using available provider with requested language persona (English or Hinglish):
    1. GEMINI_API_KEY (Google Gemini Free)
    2. GROQ_API_KEY (Groq Free)
    3. ANTHROPIC_API_KEY (Claude)
    4. Heuristic Fallback
    Dynamically injects recent exclusions from anti-repeat memory (Section 1.3)
    and pushes newly generated roast strings into rolling memory.
    """
    if not resume_text or len(resume_text.strip()) < 80:
        raise ValueError("That doesn't look like a full resume — upload the whole document.")

    lang = normalize_language(language)

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
            data = _call_gemini_api(gemini_key, resume_text, exclusion_block, language=lang)
            _validate_schema(data, resume_text, language=lang)
            _validate_no_metrics_categorization(data)
        except Exception as e:
            print(f"[WARN] Gemini API error: {e}")
            data = None

    # 2. Try Groq
    if not data and groq_key:
        try:
            data = _call_groq_api(groq_key, resume_text, exclusion_block, language=lang)
            _validate_schema(data, resume_text, language=lang)
            _validate_no_metrics_categorization(data)
        except Exception as e:
            print(f"[WARN] Groq API error: {e}")
            data = None

    # 3. Try Anthropic Claude
    if not data and anthropic_key:
        try:
            data = _call_anthropic_api(anthropic_key, resume_text, exclusion_block, language=lang)
            _validate_schema(data, resume_text, language=lang)
            _validate_no_metrics_categorization(data)
        except Exception as e:
            print(f"[WARN] Anthropic API error: {e}")
            data = None

    # 4. Fallback if external API calls fail
    if not data:
        data = _generate_fallback_roast(resume_text, exclusion_block, language=lang)
        _validate_no_metrics_categorization(data)

    # Server-side anti-repetition / duplicate check safety net (Section 3.7)
    _deduplicate_roasts(data, language=lang)

    # Push newly generated roasts into category rolling cache
    anti_repeat_memory.record_roasts(data.get("issues", []))

    # Map offsets safely
    quoted_texts = [iss["quoted_text"] for iss in data["issues"]]
    offsets = map_quoted_text_to_offsets(quoted_texts, resume_text)

    for i, issue in enumerate(data["issues"]):
        issue["start_offset"], issue["end_offset"] = offsets[i]
        issue["severity_rank"] = i + 1

    return data


def generate_roast_comeback(
    roast: dict,
    user_msg: str,
    lang: str = "hi-IN",
    history: list[dict] | None = None,
) -> str:
    """
    Generate a witty, context-grounded comeback or coaching retort when the candidate argues back.
    Uses Gemini when available, backed by an intelligent dynamic intent-driven conversational engine.
    Guarantees that consecutive responses never repeat and directly answers what the user actually asked.
    """
    verdict = roast.get("one_line_verdict", "")
    score = roast.get("overall_score", 30)
    issues = roast.get("issues", [])
    history = history or []

    # Extract past AI responses to prevent duplicate replies in the same session
    past_ai_texts = {h.get("text", "").strip() for h in history if h.get("sender") == "ai"}
    past_user_msgs = [h.get("text", "").strip().lower() for h in history if h.get("sender") == "user"]
    turn_number = len(past_user_msgs)

    # 1. Attempt LLM generation via Gemini
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key:
        candidate_models = [os.getenv("GEMINI_MODEL", "gemini-3.6-flash"), "gemini-flash-latest"]
        for model in candidate_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
                context_issues = ""
                if issues:
                    top_iss = issues[:3]
                    context_issues = "Specific resume flaws found: " + "; ".join(
                        f"Quote: '{iss.get('quoted_text', '')}' -> Rewrite: '{iss.get('fix', '')}'" for iss in top_iss
                    )

                sys_prompt = (
                    "You are a brutally honest, hilarious yet sharp tech recruiter and resume roaster in a live chat with a candidate. "
                    f"Candidate's score: {score}/100. Verdict: '{verdict}'. {context_issues}\n"
                    f"Candidate just said: '{user_msg}'.\n"
                    "Reply directly TO the candidate with a witty, savage critique or concrete advice. "
                    "Language: " + ("Conversational Hinglish with emojis" if lang == "hi-IN" else "Sharp English with emojis") + ". "
                    "Keep it strictly under 30 words. Complete sentence only, never trail off."
                )
                payload = {
                    "contents": [{"parts": [{"text": sys_prompt}]}],
                    "generationConfig": {"temperature": 0.8, "maxOutputTokens": 120},
                }
                with httpx.Client(timeout=3.5) as client:
                    resp = client.post(url, json=payload)
                    if resp.status_code == 200:
                        out = resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
                        out = out.strip('"`* \n')
                        if out and len(out) >= 20 and out not in past_ai_texts:
                            return out
            except Exception as e:
                logger.debug(f"Gemini comeback model {model} skipped: {e}")

    # 2. Intelligent, Intent-Driven Conversational Fallback Engine
    msg_l = user_msg.lower().strip()

    # Intent A: What to change / Improvement advice / "Kya badlu isme"
    if any(w in msg_l for w in ["badlu", "change", "sudhar", "improve", "kya karu", "tips", "suggestion", "kaha galti", "aur kya", "batao", "kaise", "what to fix", "what to change", "advice", "help", "next"]):
        advice_count = sum(1 for m in past_user_msgs if any(w in m for w in ["badlu", "change", "improve", "kya karu", "aur kya", "fix"]))
        if issues:
            idx = advice_count % len(issues)
            iss = issues[idx]
            flaw = iss.get("quoted_text", "").strip() or "vague bullet point"
            fix = iss.get("fix", "").strip() or "Action verb + quantifiable impact"
            if lang == "hi-IN":
                variants = [
                    f"Sabse pehle ye line dekh: '{flaw}'. Isko hata kar likh: '{fix}'. Recruiter ko measurable output chahiye, hawa-baazi nahi! 📝",
                    f"Dusri sabse badi galti: '{flaw}'. Iski jagah seedha ye daalo: '{fix}'. Isse ATS score turant jump marega! 🚀",
                    f"Ek aur blunder mila: '{flaw}'. Isko rewrite karo: '{fix}'. Numbers ke bina resume sirf biodata lagta hai! 🔥",
                    f"Bhai upar 'Download Fixed ATS (.md)' button diya hai na! Usme saare {len(issues)} flaws ka readymade solution hai, wahan se copy kar lo 📥",
                ]
                for v in variants:
                    if v not in past_ai_texts:
                        return v
                return variants[idx % len(variants)]
            else:
                variants = [
                    f"Top priority fix: replace '{flaw}' with: '{fix}'. That converts passive duties into quantifiable business impact! 📝",
                    f"Next critical fix: eliminate '{flaw}' and use: '{fix}'. ATS scans for tangible results! 🚀",
                    f"Hit the 'Download Fixed ATS (.md)' button above — all {len(issues)} flaws have full drop-in rewrites ready! 📥",
                ]
                for v in variants:
                    if v not in past_ai_texts:
                        return v
                return variants[idx % len(variants)]
        else:
            if lang == "hi-IN":
                return "Sabse pehle har bullet point ko STAR format (Situation, Task, Action, Result) mein dhalo aur % metrics add karo! 📊"
            else:
                return "Start by rewriting every bullet point with the STAR method and adding quantifiable % metrics! 📊"

    # Intent B: Agreement / "Thik hai" / "Ok" / "Got it"
    if any(w in msg_l for w in ["thik hai", "theek hai", "theek", "thik", "ok", "okay", "sahi hai", "samajh gaya", "done", "got it", "achha", "accha", "fine", "alright", "agree", "man gaya", "cool", "understood"]):
        if lang == "hi-IN":
            ok_responses = [
                "Chalo acknowledge toh kiya! Ab bas upar 'Download Fixed ATS (.md)' dabao aur apply karna shuru karo, time waste mat karo 🏃‍♂️💨",
                "Maan gaya na? Galti accept karna pehla step hai. Dusra step hai un vague bullet points ko delete karna ✂️",
                "Thik hai bolne se recruiter shortlist nahi karega bhai! Jaldi se rewrites copy karo aur resume update karo 📄⚡",
                "Good! At least denial mode se bahar aaye. Ab action lo aur agle upload mein 85+ score lake dikhao 🎯",
                "Chalo samjhdaar nikle! Ab jakar apne projects mein metrics daal do, tabhi interview call aayegi 💼",
            ]
            for r in ok_responses:
                if r not in past_ai_texts:
                    return r
            return ok_responses[turn_number % len(ok_responses)]
        else:
            ok_responses = [
                "Acknowledging it is step one! Now click 'Download Fixed ATS (.md)' and actually update your resume 🏃‍♂️💨",
                "Glad we agree. Don't just nod along — replace those passive bullet points before applying anywhere else ✂️",
                "Good to hear! Now take action so your next roast hits 85+ instead of getting filtered out by ATS 🎯",
            ]
            for r in ok_responses:
                if r not in past_ai_texts:
                    return r
            return ok_responses[turn_number % len(ok_responses)]

    # Intent C: Ambition / "Score badhaunga" / "Koshish karunga" / "Next time"
    if any(w in msg_l for w in ["koshish", "try", "badhaunga", "increase", "improve karunga", "next time", "phir se", "dobara", "agle baar", "future", "mehnat", "will try", "next upload"]):
        if lang == "hi-IN":
            ambition_responses = [
                "Koshish karne walon ki haar tab hoti hai jab wo numbers miss karte hain! Agle attempt mein exact metrics daal, 85+ score pakka hai 🎯",
                "Josh pura hai, ab thoda dimag bhi lagao! Action verbs use karo aur 2nd upload mein 80+ touch karke dikhao tab maanu 🔥",
                "Ye hui na baat! Par yaad rakhna: recruiter excuses nahi, business impact dekhta hai. Pehle 3 issues fix karo fir re-upload karna 🚀",
                f"Koshish zaroor karo bhai, par bina quantifiable data ke score {score} se 80 bhi nahi hoga! Challenge accepted? 😉",
            ]
            for r in ambition_responses:
                if r not in past_ai_texts:
                    return r
            return ambition_responses[turn_number % len(ambition_responses)]
        else:
            ambition_responses = [
                "That's the spirit! But effort without quantified metrics won't move the needle. Show me 85+ on your next upload! 🎯",
                "Challenge accepted! Replace those vague duties with business impact and prove me wrong on round 2 🔥",
            ]
            for r in ambition_responses:
                if r not in past_ai_texts:
                    return r
            return ambition_responses[turn_number % len(ambition_responses)]

    # Intent D: Numbers / Optimization / Metrics argument
    if any(w in msg_l for w in ["percent", "%", "metric", "number", "data", "optimize", "latency", "scale", "performance", "queries", "traffic"]):
        if lang == "hi-IN":
            num_responses = [
                "Bhai agar itne solid metrics the, toh resume mein dalte na! Wahan toh sirf 'helped with' likh ke hawa bana rakhi hai 😂📉",
                "Optimise toh tune kiya hoga, par bullet point mein business outcome kidhar hai? ATS numbers dhundhta hai, claims nahi 🛑",
                "Agar latency drop hui thi toh infrastructure cost kitni bachi? Adhi kahani mat sunao recruiter ko 💀",
            ]
            for r in num_responses:
                if r not in past_ai_texts:
                    return r
            return num_responses[turn_number % len(num_responses)]
        else:
            return "If those numbers were real, why are they absent from your resume? You wrote 'assisted with' instead of owning the impact 😂📉"

    # Intent E: Experience / Seniority / "Years"
    if any(w in msg_l for w in ["experience", "saal", "senior", "lead", "fresher", "college", "year", "years", "junior", "intern"]):
        if lang == "hi-IN":
            exp_responses = [
                f"{score}/100 dekh kar experience ka card mat khelo bhai! ATS ko saal nahi, measurable outcomes samajh aate hain 💀",
                "5 saal ho ya 10 saal, agar bullet point 'participated in meetings' bolega toh recruiter junior hi samjhega 📉",
                "Seniority role title se nahi, deliverables se dikhti hai. Resume ke pehle do points mein apna biggest win highlight karo 💼",
            ]
            for r in exp_responses:
                if r not in past_ai_texts:
                    return r
            return exp_responses[turn_number % len(exp_responses)]
        else:
            return f"Years of experience mean nothing if you can't quantify impact. ATS filters keywords, not excuses! Score {score}/100 stands 💀"

    # Intent F: Disbelief / Calling Roast Fake / Wrong
    if any(w in msg_l for w in ["fake", "galat", "wrong", "lie", "jhooth", "bakwas", "bekar", "pagal", "chup", "shut up"]):
        if lang == "hi-IN":
            fake_responses = [
                "Hum jhooth bol rahe hain ya tera bullet point? Recruiter ko 6 second lagte hain reject dabane mein, debate ka time nahi milta wahan 🛑",
                "Gussa aana natural hai bhai, sach kadwa hota hai! Par yahan ladne se achha hai flaws rewrite kar lo ☕",
                "Reality check ko 'galat' bolne se rejection email offer letter mein nahi badal jayega 😉",
            ]
            for r in fake_responses:
                if r not in past_ai_texts:
                    return r
            return fake_responses[turn_number % len(fake_responses)]
        else:
            return "Denial won't turn a rejection email into an interview. The flaws are grounded right in what you wrote! 🛑"

    # Intent G: Greetings / Short Casual
    if any(w in msg_l for w in ["hi", "hello", "hey", "namaste", "suno", "kaise ho", "yo", "sup", "bhai"]) and len(msg_l.split()) <= 3:
        if lang == "hi-IN":
            return f"Haan bhai bolo! Score {score}/100 dekh kar dil toota ya reality check mila? Batao kahan se shuru karein 😈"
        else:
            return f"Welcome! Roasted you at {score}/100 — what part of your resume are we defending today? 😈"

    # Intent H: General Dynamic Pool (Guaranteed Non-Repeating)
    if lang == "hi-IN":
        gen_responses = [
            f"Itna confidence agar resume ke summary section mein dikhaya hota toh score {score} nahi, 85+ hota! 😉",
            f"Tere is defense ko hum 10/10 dete hain, par resume ka score abhi bhi {score}/100 hi rahega jab tak rewrites apply nahi karoge! 😈",
            "Bhai point tera valid ho sakta hai, lekin ATS scanner ko logic nahi, exact action verbs aur numbers samajh aate hain 📉",
            "Kaash recruiter ko bhi phone karke ye sab samjha paate! Isliye bol rahe hain, sab kuch resume par quantifiable likho 📄",
            f"Score {score}/100 badhana hai toh yahan debate chhod ke upar 'Download Fixed ATS (.md)' check karo, wahan solution ready hai! 💡",
            "Defense accha hai bhai, par recruiter 6 seconds mein reject kar deta hai. Action verbs add karo aur dubara aao 🔥",
            "Dil par mat le bhai, ye roast tere bhale ke liye tha! Galtiyan sudhar aur mast package nikal 💼🚀",
        ]
        for r in gen_responses:
            if r not in past_ai_texts:
                return r
        return gen_responses[(turn_number + hash(user_msg)) % len(gen_responses)]
    else:
        gen_responses = [
            f"Great comeback! If only half that energy went into writing actionable bullet points instead of generic corporate jargon 😈🔥",
            f"Your defense is entertaining, but ATS doesn't interview your personality. Score {score}/100 stands until you rewrite! 📉",
            "Save the debate for the actual interview! Use the 'Download Fixed ATS (.md)' button above to fix the flagged lines 💡",
            f"Confidence is 10/10, but resume execution is {score}/100. Add quantified outcomes and try again! 🎯",
        ]
        for r in gen_responses:
            if r not in past_ai_texts:
                return r
        return gen_responses[(turn_number + hash(user_msg)) % len(gen_responses)]

