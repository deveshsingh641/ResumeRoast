"""Prompt registry: language code → dedicated persona templates (no inline conditionals)."""

from __future__ import annotations

from app.i18n.mapping import DEFAULT_LANGUAGE, normalize_language
from app.prompts import en as en_prompts
from app.prompts import hi_IN as hi_prompts

from datetime import datetime

_PROMPT_MODULES = {
    "en": en_prompts,
    "hi-IN": hi_prompts,
}


def get_temporal_context(language: str | None = None) -> str:
    """Generate dynamic temporal & calendar reality check instructions."""
    now = datetime.now()
    month_year = now.strftime("%B %Y")
    current_year = now.year
    lang = normalize_language(language)
    if lang == "hi-IN":
        return (
            f"TEMPORAL & CALENDAR REALITY CHECK (CRITICAL):\n"
            f"- Aaj ki real-world current date hai: {month_year} (Year {current_year}).\n"
            f"- {current_year} ya usse pehle ke saare years ({current_year}, {current_year - 1}, {current_year - 2}, etc.) aur months already PAST ya PRESENT hain.\n"
            f"- KISI BHI DATE KO jo {month_year} ya usse pehle ki ho (jaise {current_year} ki internships ya experiences), galti se bhi 'future', 'time machine', 'time travel', ya 'future se resume forward' bolke roast MAT KARNA. Ye dates real-world mein ho chuki hain!\n"
            f"- College graduation / degrees ke aage ke saal (jaise {current_year + 1}, {current_year + 2}, ya 'Expected {current_year + 1}') standard prospective graduation timelines hain — unhe time travel mat bolna.\n"
            f"- Date pe roast tabhi karo agar obvious logical contradiction ho (e.g. Start date 2025 aur End date 2023) ya koi fake saal ho (jaise 2099)."
        )
    else:
        return (
            f"TEMPORAL & CALENDAR REALITY CHECK (CRITICAL):\n"
            f"- Today's real-world current date is: {month_year} (Year {current_year}).\n"
            f"- Any date, month, or year on or before {month_year} (including {current_year}, {current_year - 1}, {current_year - 2}, etc.) is already in the PAST or PRESENT.\n"
            f"- NEVER mock or roast dates on or before {month_year} (such as experiences in {current_year}) as 'future', 'time machine', 'time travel', or 'forwarding from the future'. They are valid historical/current dates!\n"
            f"- Prospective graduation years for college degrees (e.g. {current_year + 1}, {current_year + 2}, or 'Expected {current_year + 1}') are standard for students — do NOT roast them as time travel.\n"
            f"- Only roast date ranges if there is an actual logical contradiction (e.g. End date earlier than Start date like '2025 - 2023') or an impossible century."
        )


def get_system_prompt(language: str | None) -> str:
    lang = normalize_language(language)
    module = _PROMPT_MODULES.get(lang, _PROMPT_MODULES[DEFAULT_LANGUAGE])
    return f"{module.SYSTEM_PROMPT}\n\n{get_temporal_context(lang)}"


def get_user_prompt_template(language: str | None) -> str:
    lang = normalize_language(language)
    module = _PROMPT_MODULES.get(lang, _PROMPT_MODULES[DEFAULT_LANGUAGE])
    now = datetime.now()
    month_year = now.strftime("%B %Y")
    # Pre-fill current_date so callers doing .format(resume_text=..., exclusion_block=...)
    # are completely backwards compatible and don't trigger KeyError
    return module.USER_PROMPT_TEMPLATE.replace("{current_date}", month_year)


def get_battle_system_prompt(language: str | None) -> str:
    """Dedicated battle addendum per language, stacked on that language's roast persona."""
    lang = normalize_language(language)
    base = get_system_prompt(lang)
    if lang == "hi-IN":
        extra = """

BATTLE MODE RULES:
You are now refereeing a 1-on-1 Resume Roast Battle between Fighter 1 and Fighter 2.
You have the already-analyzed structured scores and issues for both candidates.
Compare them savagely in natural WhatsApp-style Hinglish Roman script.

Rules:
- Declare a clear winner ("fighter_1", "fighter_2", or "draw") based on the higher score and fewer catastrophic flaws.
- Margin must be "landslide" (score diff > 20), "close" (score diff 5-20), or "draw" (score diff < 5).
- Write a 2-3 sentence savage verdict in Hinglish comparing their choices. Ground the commentary in their actual scores and quotes.
- Give a punchy best_line for each fighter (praise if strong, hilarious roast callout if weak).

RETURN EXACTLY THIS JSON SCHEMA:
{
  "winner": "<fighter_1 | fighter_2 | draw>",
  "margin": "<landslide | close | draw>",
  "verdict": "<2-3 sentence savage comparative commentary in Hinglish with 1-2 emojis>",
  "fighter_1_best_line": "<single sharpest praise or roast for fighter 1>",
  "fighter_2_best_line": "<single sharpest praise or roast for fighter 2>"
}
"""
    else:
        extra = """

BATTLE MODE RULES:
You are now refereeing a 1-on-1 Resume Roast Battle between Fighter 1 and Fighter 2.
You have the already-analyzed structured scores and issues for both candidates.
Compare them in witty, direct English — roast the writing, never the people.

Rules:
- Declare a clear winner ("fighter_1", "fighter_2", or "draw") based on the higher score and fewer catastrophic flaws.
- Margin must be "landslide" (score diff > 20), "close" (score diff 5-20), or "draw" (score diff < 5).
- Write a 2-3 sentence savage verdict in English comparing their choices. Ground the commentary in their actual scores and quotes.
- Give a punchy best_line for each fighter (praise if strong, hilarious roast callout if weak).

RETURN EXACTLY THIS JSON SCHEMA:
{
  "winner": "<fighter_1 | fighter_2 | draw>",
  "margin": "<landslide | close | draw>",
  "verdict": "<2-3 sentence savage comparative commentary in English with 1-2 emojis>",
  "fighter_1_best_line": "<single sharpest praise or roast for fighter 1>",
  "fighter_2_best_line": "<single sharpest praise or roast for fighter 2>"
}
"""
    return base + extra
