"""Per-language joke banks used by anti-repeat memory and heuristic fallback."""

from __future__ import annotations

from app.i18n.mapping import DEFAULT_LANGUAGE, normalize_language
from app.services.anti_repeat_service import BASELINE_JOKE_BANKS

ENGLISH_JOKE_BANKS: dict[str, list[str]] = {
    "no-metrics": [
        "How many? What happened? This line has a verb and a shrug.",
        "There's a claim in here, but the number went out for lunch 👀",
        "'Improved performance' — by 2% or 200%? Those are different careers.",
        "I believe you did the work. I cannot prove it from this sentence 😅",
        "Put a number in or this is just atmosphere.",
        "This reads like a poem about your job, not evidence of it 📝",
        "Data, please — the plot summary isn't landing 📊",
        "How many users or requests? Zero numbers and the recruiter keeps scrolling.",
        "This isn't a thriller. Say the scale out loud 📉",
        "A whole paragraph and not one metric. Bold strategy 🤷‍♂️",
        "Without data this claim is mostly weather 💨",
        "Where's the impact? Recruiters didn't bring a calculator to imagine it 🧮",
        "Exact numbers: how much faster, how much bigger?",
        "Solid work maybe — unprovable from this line 📈",
        "Six seconds to find a number. Yours went missing.",
    ],
    "buzzword": [
        "Every resume on earth says this. Recruiters stopped reading it as information around 2015.",
        "You used the word. Now show the work.",
        "This line has LinkedIn's fingerprint on it 😅",
        "More generic than a weather report, and those at least have numbers.",
        "This adjective is doing a lot of unpaid overtime.",
        "You're blending into the pile that used the same phrase this morning.",
        "We know. You didn't need to announce the personality trait 🙃",
        "Adjectives don't get interviews. Outcomes do.",
        "Feels like a random pull from the corporate dictionary 🤖",
        "Heavy vocabulary doesn't shortlist you — the actual work does 🗣️",
        "This reads like ChatGPT had no context and a deadline 🧠",
        "This much fluff and the recruiter needs a window 😵",
        "Buzzword festival in a single bullet 🎪",
        "Stop talking like a thought-leader carousel. Say what shipped 📉",
        "This phrase expired around 2018 ⏳",
    ],
    "formatting": [
        "The spacing says this was finished at 11:58pm 😬",
        "Font this small and the recruiter is hunting for glasses 🔍",
        "Alignment's off — resume or jigsaw puzzle?",
        "Too many fonts. This looks like a ransom note that went to business school 🗞️",
        "Bullet sizes aren't even on speaking terms.",
        "Margins so tight the page can't breathe 😮💨",
        "Spacing looks like the elements are in a feud 🥊",
        "Visual hierarchy went on vacation. Where do we look?",
        "You murdered the whitespace on this page 🪓",
        "So cramped the recruiter's eyes will file overtime 😵",
        "Header smaller than body copy? That's not a hierarchy 📐",
        "Pick one indent and commit. This is a different indent per mood.",
    ],
    "length": [
        "Nobody is doing a PhD in your CV 📚",
        "Everything stuffed onto one page like a junk drawer 🫠",
        "You wrote a lot and said almost nothing.",
        "They don't need the director's cut. Cut to the point.",
        "Recruiters give this six seconds. You gave them six pages.",
        "Shorter and sharper — this isn't an essay.",
        "Four pages? That's a novella with bullet points 📖",
        "Cut childhood schooling. Stay on the work that matters.",
        "They'll be tired before page two. Make a one-page draft 📄",
        "Longer resume, smaller odds — ugly, but usually true.",
        "Nobody is finishing this summary. Two lines. Max.",
        "Crisp bullets. This is not an autobiography.",
    ],
    "irrelevant": [
        "Why is this here? It has nothing to do with the job 🤔",
        "Cool college fest. Still not a job bullet.",
        "Was this detail required, or did it just wander in?",
        "No connection to the role — cut it.",
        "A recruiter does not need to know this.",
        "This line is renting space it hasn't earned.",
        "This isn't a marriage biodata — hobbies and blood type can go 😅",
        "Declarations and signatures retired in 2005 ✋",
        "This line confuses the role you're even applying for.",
        "Cut the noise. Put a live GitHub or portfolio link here 🔗",
        "Don't spend premium whitespace on zero-weight trivia.",
        "Delete hobbies. Add one real open-source or shipped project.",
    ],
    "typo": [
        "Spellcheck exists. This line didn't meet it 😩",
        "One typo and 'detail-oriented' becomes a joke at your expense.",
        "Small mistake, huge first impression.",
        "Proofread once more. Your future self will send a thank-you.",
        "Recruiters find the typo before they find the achievement.",
        "Spelled like autocorrect already surrendered 🤡",
        "Typos in the tech stack? At least spell Python correctly.",
        "Looks like it was submitted unread.",
        "Grammarly is free and faster than a rejection ⏱️",
        "A typo is the easiest excuse to hit reject.",
    ],
    "other": [
        "I read this twice and still don't know what you did.",
        "Something's off and I can't pin the crime yet.",
        "This needed one more clause and then it left the building.",
        "Say the thing. Don't orbit it.",
        "This belongs somewhere else, or nowhere.",
        "This bullet has neither a head nor a tail. What were you trying to say?",
        "Vague. Lead with a real action verb.",
        "The claim walks offstage before the punchline.",
        "Feels like a sentence got cut mid-thought. Re-read it.",
        "Overcomplicated. Plain English would do more work.",
    ],
}

JOKE_BANKS_BY_LANGUAGE: dict[str, dict[str, list[str]]] = {
    "hi-IN": BASELINE_JOKE_BANKS,
    "en": ENGLISH_JOKE_BANKS,
}


def get_joke_banks(language: str | None) -> dict[str, list[str]]:
    lang = normalize_language(language)
    return JOKE_BANKS_BY_LANGUAGE.get(lang, JOKE_BANKS_BY_LANGUAGE[DEFAULT_LANGUAGE])
