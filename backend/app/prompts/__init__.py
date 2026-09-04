"""Prompt registry: language code → dedicated persona templates (no inline conditionals)."""

from __future__ import annotations

from app.i18n.mapping import DEFAULT_LANGUAGE, normalize_language
from app.prompts import en as en_prompts
from app.prompts import hi_IN as hi_prompts

_PROMPT_MODULES = {
    "en": en_prompts,
    "hi-IN": hi_prompts,
}


def get_system_prompt(language: str | None) -> str:
    lang = normalize_language(language)
    module = _PROMPT_MODULES.get(lang, _PROMPT_MODULES[DEFAULT_LANGUAGE])
    return module.SYSTEM_PROMPT


def get_user_prompt_template(language: str | None) -> str:
    lang = normalize_language(language)
    module = _PROMPT_MODULES.get(lang, _PROMPT_MODULES[DEFAULT_LANGUAGE])
    return module.USER_PROMPT_TEMPLATE


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
