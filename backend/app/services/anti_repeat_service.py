"""
Anti-Repetition Memory Service for Resume Roast
Maintains category-keyed rolling caches (Redis + in-memory fallback) to prevent
cross-session joke repetition and injects dynamic exclusion lists into AI prompts.
"""
from __future__ import annotations

import collections
import os
import random
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Maximum lines stored per category (trimmed oldest-first)
MAX_CACHE_PER_CATEGORY = 40

# Default sample size of recent jokes to exclude in prompt
DEFAULT_EXCLUSION_SAMPLE = 6

# ---------------------------------------------------------------------------
# Section 1.2 Baseline Joke Banks per Category
# ---------------------------------------------------------------------------
BASELINE_JOKE_BANKS: dict[str, list[str]] = {
    "no-metrics": [
        "Kitna kiya bhai, number bata na.",
        "Number nahi hai isme, chhupa kyun rahe ho? 👀",
        "'Improved performance' — improved kitna, 2% ya 200%? Bahut fark hai bhai.",
        "Isse padh ke lagta hai kaam toh kiya, bas gine nahi kabhi 😅",
        "Number daal do bas, itna hi kehna hai.",
        "Bina number ke ye line resume mein hai ya shayari mein, samajh nahi aa raha 📝",
        "Data do yaar, story nahi chahiye humein 📊",
        "Kitne users ya requests handle kiye bhai? Zero number dekh ke recruiter aage badh jayega.",
        "Suspense movie nahi hai bhai, scale kitna kiya khul ke batao 📉",
        "Pura paragraph likh diya par metric ek bhi nahi, kamaal hai yaar 🤷‍♂️",
        "Bina data ke ye claim hawa-hawaai lag raha hai boss 💨",
        "Impact kahan hai bhai? Recruiter calculator leke nahi baithega 🧮",
        "Exact numbers daalo: kitne percent speed badhayi ya kitna scale kiya?",
        "Kaam solid kiya hoga par bina numbers ke prove kaise karoge? 📈",
        "Recruiter 6 second mein number dhundhta hai, aur yahan number hi gayab hai.",
    ],
    "buzzword": [
        "Ye word har second resume mein hai bhai, tu unique kaise banega isse?",
        "Buzzword daal diya, ab kaam bhi dikha do na.",
        "Ye line copy-paste lagti hai, LinkedIn se utha li kya? 😅",
        "Itna generic hai ye, isse toh weather report zyada specific hoti hai.",
        "Ye word suna-suna sa lagta hai bhai, naya kuch socho.",
        "Har resume mein ye milega, tu bhi unme se ek lag raha hai abhi.",
        "Sabko pata hai tu ye ho, likhna zaroori nahi tha 🙃",
        "Ye adjective proof nahi maangta, achievement maangta hai.",
        "Corporate dictionary se random word utha ke chipka diya lagta hai 🤖",
        "Heavy vocabulary se shortlist nahi hoti bhai, simple sach bolo 🗣️",
        "Ye padh ke lag raha hai resume ChatGPT ne bina context ke likha hai 🧠",
        "Itna corporate fluff padh ke recruiter ka sir ghoom jayega 😵",
        "Buzzword festival chal raha hai kya is bullet point mein? 🎪",
        "LinkedIn influencers ki tarah bolna band karo, asli kaam batao 📉",
        "Ye phrase 2018 mein hi expire ho gaya tha bhai ⏳",
    ],
    "formatting": [
        "Spacing dekh ke lag raha hai jaldi mein banaya tha resume 😬",
        "Font size itni chhoti hai, recruiter chashma dhundhega 🔍",
        "Alignment off hai bhai, ye resume hai ya jigsaw puzzle?",
        "Itne fonts use kar diye, ransom note jaisa lag raha hai 🗞️",
        "Bullet points ka size hi consistent nahi hai yaar.",
        "Margins itne tight hain, resume saans nahi le pa raha 😮💨",
        "Spacing aisi hai jaise elements ek dusre se ladai karke baithe hon 🥊",
        "Visual hierarchy ki aisi-taisi kar di bhai, kahan dekhna hai samajh nahi aa raha.",
        "Whitespace ka murder kar diya hai tune is page pe 🪓",
        "Lines itni cramped hain, padhte-padhte recruiter ki aankh dukhne lagegi 😵",
        "Header ka font size body se chhota kaise ho gaya bhai? 📐",
        "Different indent levels kyu hain har bullet mein? Ek standard follow karo.",
    ],
    "length": [
        "Itna lamba kar diya, recruiter ke paas PhD karne ka time nahi hai isko padhne ke liye 📚",
        "Ek page mein sab thoonsa hua hai, Diwali ke baad ka WhatsApp status jaisa lag raha hai 🪔",
        "Bahut kuch likh diya, matlab kuch nahi mila padhne ko.",
        "Itni detail kisi ko nahi chahiye bhai, seedha point pe aao.",
        "Recruiter 6 second dekhta hai resume, tune usse 6 page bana diya.",
        "Chota aur sharp likho, ye essay nahi hai.",
        "4 page ka resume? Novel likh rahe ho kya boss? 📖",
        "Purani schooling aur bachpan ki baatein hatao, relevant cheez pe focus karo.",
        "Recruiter scroll karte karte thak jayega, 1-page crisp draft banao 📄",
        "Jitna lamba resume, utna kam chance shortlist hone ka — rule of thumb hai.",
        "Itni lambi summary kaun padhta hai yaar? 2 lines mein wrap karo.",
        "Crisp bullets banao, ye autobiography nahi hai.",
    ],
    "irrelevant": [
        "Ye yahan kyun hai bhai? Iska job se koi lena dena nahi 🤔",
        "College fest mein volunteer kiya tha, but yahan uska kya kaam?",
        "Ye detail resume mein daalna zaroori tha kya, seriously?",
        "Iska is role se koi connection nahi bhai, hata do.",
        "Recruiter ko iske baare mein janna hi nahi hai.",
        "Space waste ho raha hai is line pe, kuch relevant daalo.",
        "Shaadi ka biodata thodi hai jo hobbies aur blood group daal rahe ho 😅",
        "Declaration aur signatures 2005 mein hi obsolete ho chuke the ✋",
        "Ye line padh ke recruiter confuse ho jayega ki apply kis role ke liye kiya hai.",
        "Irrelevant points hatao aur wahan live GitHub ya portfolio links daalo 🔗",
        "Valuable white space aisi information pe waste mat karo jiska zero weightage hai.",
        "Hobbies section delete karke ek solid open-source project add karo.",
    ],
    "typo": [
        "Spelling mistake hai bhai, spellcheck bhi nahi chalaya kya? 😩",
        "Ek typo dikh gaya, recruiter ko lagega detail-oriented nahi ho.",
        "Ye galti chhoti lagti hai but bahut bada impression banati hai galat.",
        "Proofread karna bhool gaye kya, ek baar aur padh lo.",
        "Chhoti si galti hai, but recruiter ki nazar pehle yahi jaati hai.",
        "Spelling aisi likhi hai jaise auto-correct ne bhi haar maan li ho 🤡",
        "Tech stack ke naam mein typo? Python aur JavaScript ki spelling toh theek likho!",
        "Ek spelling mistake se lagta hai bina padhe submit kar diya tha.",
        "Grammarly ya free spellchecker run karne mein kitna time lagta hai bhai? ⏱️",
        "Recruiter ko typo milte hi reject button dabane ka bahana mil jaata hai.",
    ],
    "other": [
        "Ye line samajh nahi aayi bhai, tum khud padh ke bataoge?",
        "Kuch toh gadbad hai isme, par pin nahi kar pa raha exactly kya.",
        "Ye reh gaya explain kiye bina, thoda clarify karo.",
        "Iska matlab nikal nahi raha, seedha likho.",
        "Ye jagah out of place lag rahi hai bhai.",
        "Is bullet point ka na sar hai na pair, seedha likho na kya kehna chahte ho.",
        "Thoda vague lag raha hai ye statement, clear action verb use karo.",
        "Ye claim adha-adhura sa chhod diya hai, conclusion kahan hai?",
        "Padh ke lagta hai kuch miss ho gaya yahan, ek baar re-read karo.",
        "Ye sentence over-complicated hai, simple English mein bolo.",
    ],
}

# ---------------------------------------------------------------------------
# Storage Engine: Redis with In-Memory Fallback
# ---------------------------------------------------------------------------
class AntiRepeatMemory:
    def __init__(self) -> None:
        self._redis_client = None
        self._in_memory: dict[str, collections.deque[str]] = {
            cat: collections.deque(maxlen=MAX_CACHE_PER_CATEGORY)
            for cat in BASELINE_JOKE_BANKS
        }
        self._init_redis()

    def _init_redis(self) -> None:
        redis_url = os.getenv("REDIS_URL", "").strip()
        if redis_url:
            try:
                import redis
                client = redis.from_url(redis_url, decode_responses=True, socket_timeout=2.0)
                client.ping()
                self._redis_client = client
            except Exception as e:
                self._redis_client = None

    def record_roast(self, category: str, roast_text: str) -> None:
        """Pushes a newly generated roast line into the category cache and trims oldest."""
        clean_text = roast_text.strip()
        if not clean_text or len(clean_text) < 5:
            return

        cat_key = category if category in BASELINE_JOKE_BANKS else "other"

        # 1. Update in-memory fallback
        if cat_key not in self._in_memory:
            self._in_memory[cat_key] = collections.deque(maxlen=MAX_CACHE_PER_CATEGORY)
        # Avoid duplicate inside deque if already most recent
        if not self._in_memory[cat_key] or self._in_memory[cat_key][-1] != clean_text:
            self._in_memory[cat_key].append(clean_text)

        # 2. Update Redis if active
        if self._redis_client:
            try:
                redis_key = f"recent_roasts:{cat_key}"
                self._redis_client.lpush(redis_key, clean_text)
                self._redis_client.ltrim(redis_key, 0, MAX_CACHE_PER_CATEGORY - 1)
            except Exception:
                # Redis dropped; in-memory cache remains functional
                pass

    def record_roasts(self, issues: list[dict]) -> None:
        """Records all roasts from a generated analysis response."""
        for issue in issues:
            if isinstance(issue, dict):
                cat = str(issue.get("category", "other")).lower().strip()
                roast = str(issue.get("roast", "")).strip()
                if roast:
                    self.record_roast(cat, roast)

    def get_recent_roasts(self, category: Optional[str] = None) -> list[str]:
        """Returns recent roasts for a specific category or aggregated across all."""
        if category and category in BASELINE_JOKE_BANKS:
            if self._redis_client:
                try:
                    redis_key = f"recent_roasts:{category}"
                    items = self._redis_client.lrange(redis_key, 0, MAX_CACHE_PER_CATEGORY - 1)
                    if items:
                        return list(items)
                except Exception:
                    pass
            return list(self._in_memory.get(category, []))

        # Aggregate across all categories
        aggregated: list[str] = []
        for cat in BASELINE_JOKE_BANKS:
            lines = self.get_recent_roasts(cat)
            aggregated.extend(lines)
        return aggregated

    def get_sample_exclusions(
        self,
        categories: Optional[list[str]] = None,
        sample_size: int = DEFAULT_EXCLUSION_SAMPLE,
    ) -> list[str]:
        """
        Pulls a random sample of 5-8 recently used lines from specified categories
        or across all categories if none specified.
        """
        pool: list[str] = []
        target_cats = categories if categories else list(BASELINE_JOKE_BANKS.keys())

        for cat in target_cats:
            recent = self.get_recent_roasts(cat)
            pool.extend(recent)

        # De-duplicate preserving order
        unique_pool = list(dict.fromkeys(pool))

        if not unique_pool:
            return []

        sample_k = min(sample_size, len(unique_pool))
        return random.sample(unique_pool, sample_k)

    def build_exclusion_prompt(
        self,
        categories: Optional[list[str]] = None,
        sample_size: int = DEFAULT_EXCLUSION_SAMPLE,
    ) -> str:
        """
        Formats the dynamic exclusion block to be injected into AI analysis prompts.
        """
        exclusions = self.get_sample_exclusions(categories=categories, sample_size=sample_size)
        if not exclusions:
            return ""

        bullet_lines = "\n".join(f'- "{line}"' for line in exclusions)
        return (
            "The following lines have been used recently — do NOT reuse these or\n"
            "anything closely resembling them, generate genuinely different jokes:\n"
            f"{bullet_lines}"
        )

    def clear(self) -> None:
        """Clears both in-memory and Redis caches (for testing)."""
        for deque_list in self._in_memory.values():
            deque_list.clear()
        if self._redis_client:
            try:
                for cat in BASELINE_JOKE_BANKS:
                    self._redis_client.delete(f"recent_roasts:{cat}")
            except Exception:
                pass


# Global singleton instance
anti_repeat_memory = AntiRepeatMemory()
