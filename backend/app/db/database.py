"""
Database client — Supabase/PostgreSQL in production, in-memory fallback for local dev.
Includes UTC daily usage counters, 7-day expiry enforcement, and deduplication caching.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple
from uuid import uuid4

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
ANONYMOUS_ROAST_EXPIRY_DAYS = int(os.getenv("ANONYMOUS_ROAST_EXPIRY_DAYS", "7"))
FREE_TIER_DAILY_LIMIT = int(os.getenv("FREE_TIER_DAILY_LIMIT", "1"))

# In-memory stores
_memory_store: dict[str, dict] = {}
_usage_memory: dict[str, int] = {}  # key -> count for today (UTC)
_dedup_cache: dict[str, tuple[float, str]] = {}  # content_hash -> (timestamp, roast_id)
_reactions_memory: dict[str, dict[str, int]] = {}  # roast_id -> {emoji: count}


def _get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    stripe_customer_id TEXT,
    subscription_status TEXT NOT NULL DEFAULT 'free'
);

CREATE TABLE IF NOT EXISTS roasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    device_fingerprint TEXT,
    overall_score INTEGER NOT NULL,
    band TEXT NOT NULL,
    one_line_verdict TEXT NOT NULL,
    issues JSONB NOT NULL DEFAULT '[]',
    strengths JSONB NOT NULL DEFAULT '[]',
    voice_script TEXT,
    voice_audio_path TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS battles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fighter_1_score INTEGER NOT NULL,
    fighter_1_band TEXT NOT NULL,
    fighter_1_verdict TEXT NOT NULL,
    fighter_1_issues JSONB NOT NULL DEFAULT '[]',
    fighter_1_strengths JSONB NOT NULL DEFAULT '[]',
    fighter_2_score INTEGER NOT NULL,
    fighter_2_band TEXT NOT NULL,
    fighter_2_verdict TEXT NOT NULL,
    fighter_2_issues JSONB NOT NULL DEFAULT '[]',
    fighter_2_strengths JSONB NOT NULL DEFAULT '[]',
    winner TEXT NOT NULL,
    margin TEXT NOT NULL,
    verdict TEXT NOT NULL,
    fighter_1_best_line TEXT NOT NULL,
    fighter_2_best_line TEXT NOT NULL,
    device_fingerprint TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS wall_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roast_id UUID,
    type TEXT NOT NULL,
    score INTEGER NOT NULL,
    band TEXT NOT NULL,
    one_line_verdict TEXT NOT NULL,
    top_roast_lines JSONB NOT NULL DEFAULT '[]',
    flag_count INTEGER NOT NULL DEFAULT 0,
    hidden BOOLEAN NOT NULL DEFAULT FALSE,
    device_fingerprint TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS usage_counters (
    id SERIAL PRIMARY KEY,
    key TEXT NOT NULL,
    date DATE NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    UNIQUE(key, date)
);

CREATE TABLE IF NOT EXISTS roast_reactions (
    id SERIAL PRIMARY KEY,
    roast_id TEXT NOT NULL,
    emoji TEXT NOT NULL,
    count INTEGER NOT NULL DEFAULT 0,
    UNIQUE (roast_id, emoji)
);

CREATE INDEX IF NOT EXISTS idx_roasts_expires_at ON roasts (expires_at);
CREATE INDEX IF NOT EXISTS idx_battles_expires_at ON battles (expires_at);
CREATE INDEX IF NOT EXISTS idx_wall_type_score ON wall_entries (type, hidden, score, created_at);
CREATE INDEX IF NOT EXISTS idx_roast_reactions_roast_id ON roast_reactions (roast_id);
"""


def init_db() -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    if not DATABASE_URL:
        return
    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
            conn.commit()
    except Exception as e:
        print(f"[WARN] DB init error: {e}")


def check_dedup(content_hash: str) -> Optional[str]:
    """
    Check if an identical document was submitted in the last 60 seconds.
    Returns existing roast_id if found, avoiding double billing / redundant processing.
    """
    now = time.time()
    if content_hash in _dedup_cache:
        ts, roast_id = _dedup_cache[content_hash]
        if now - ts < 60:
            return roast_id
        else:
            del _dedup_cache[content_hash]
    return None


def register_dedup(content_hash: str, roast_id: str) -> None:
    """Register content hash for 60-second debounce window."""
    _dedup_cache[content_hash] = (time.time(), roast_id)


def save_roast(
    *,
    overall_score: int,
    band: str,
    one_line_verdict: str,
    issues: list,
    strengths: list,
    user_id: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
) -> str:
    """Persist a roast result and return its UUID string."""
    roast_id = str(uuid4())
    now_utc = datetime.now(timezone.utc)
    expires_at = None

    if user_id is None:
        # Anonymous roasts expire after exactly 7 days
        expires_at = (now_utc + timedelta(days=ANONYMOUS_ROAST_EXPIRY_DAYS)).isoformat()

    if not DATABASE_URL:
        _memory_store[roast_id] = {
            "id": roast_id,
            "user_id": user_id,
            "overall_score": overall_score,
            "band": band,
            "one_line_verdict": one_line_verdict,
            "issues": issues,
            "strengths": strengths,
            "created_at": now_utc.isoformat(),
            "expires_at": expires_at,
        }
        return roast_id

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO roasts
                  (id, user_id, device_fingerprint, overall_score, band,
                   one_line_verdict, issues, strengths, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    roast_id,
                    user_id,
                    device_fingerprint,
                    overall_score,
                    band,
                    one_line_verdict,
                    json.dumps(issues),
                    json.dumps(strengths),
                    expires_at,
                ),
            )
        conn.commit()
    return roast_id


def get_roast(roast_id: str) -> Optional[dict]:
    """Fetch a roast by ID. Returns None if not found or expired."""
    now_utc = datetime.now(timezone.utc).isoformat()

    if not DATABASE_URL:
        data = _memory_store.get(roast_id)
        if not data:
            return None
        if data.get("expires_at") and data["expires_at"] < now_utc:
            del _memory_store[roast_id]
            return None
        return data

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM roasts
                WHERE id = %s
                  AND (expires_at IS NULL OR expires_at > now())
                """,
                (roast_id,),
            )
            row = cur.fetchone()
    return dict(row) if row else None


def cleanup_expired_roasts() -> int:
    """Purge all expired roasts per 7-day retention policy. Returns count removed."""
    now_utc = datetime.now(timezone.utc).isoformat()
    removed = 0

    if not DATABASE_URL:
        expired_keys = [
            k for k, v in _memory_store.items()
            if v.get("expires_at") and v["expires_at"] < now_utc
        ]
        for k in expired_keys:
            del _memory_store[k]
            removed += 1
        return removed

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM roasts WHERE expires_at IS NOT NULL AND expires_at < now()")
            removed = cur.rowcount
        conn.commit()
    return removed


def get_usage_count(key: str) -> int:
    """Return how many roasts 'key' has performed today in UTC."""
    today_utc = datetime.now(timezone.utc).date().isoformat()
    if not DATABASE_URL:
        return _usage_memory.get(f"{key}:{today_utc}", 0)

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count FROM usage_counters WHERE key = %s AND date = %s",
                (key, today_utc),
            )
            row = cur.fetchone()
    return row["count"] if row else 0


def increment_usage(key: str) -> int:
    """Increment today's usage count for key in UTC."""
    today_utc = datetime.now(timezone.utc).date().isoformat()
    mem_key = f"{key}:{today_utc}"

    if not DATABASE_URL:
        _usage_memory[mem_key] = _usage_memory.get(mem_key, 0) + 1
        return _usage_memory[mem_key]

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO usage_counters (key, date, count)
                VALUES (%s, %s, 1)
                ON CONFLICT (key, date) DO UPDATE
                  SET count = usage_counters.count + 1
                RETURNING count
                """,
                (key, today_utc),
            )
            new_count = cur.fetchone()["count"]
        conn.commit()
    return new_count


# ---------------------------------------------------------------------------
# User & Subscription Helpers
# ---------------------------------------------------------------------------
_users_memory: dict[str, dict] = {}


def create_or_get_user(email: str) -> dict:
    """Get or create user record by email."""
    now_utc = datetime.now(timezone.utc).isoformat()
    if not DATABASE_URL:
        if email not in _users_memory:
            user_id = str(uuid4())
            _users_memory[email] = {
                "id": user_id,
                "email": email,
                "created_at": now_utc,
                "stripe_customer_id": None,
                "subscription_status": "free",
            }
        return _users_memory[email]

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            if row:
                return dict(row)
            user_id = str(uuid4())
            cur.execute(
                """
                INSERT INTO users (id, email, subscription_status, created_at)
                VALUES (%s, %s, 'free', %s)
                RETURNING *
                """,
                (user_id, email, now_utc),
            )
            created = cur.fetchone()
        conn.commit()
    return dict(created)


def update_subscription(email: str, status: str, customer_id: Optional[str] = None) -> None:
    """Update subscription status for user."""
    if not DATABASE_URL:
        user = create_or_get_user(email)
        user["subscription_status"] = status
        if customer_id:
            user["stripe_customer_id"] = customer_id
        return

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET subscription_status = %s,
                    stripe_customer_id = COALESCE(%s, stripe_customer_id)
                WHERE email = %s
                """,
                (status, customer_id, email),
            )
        conn.commit()


def get_user_subscription(email: str) -> str:
    """Check subscription status for user email."""
    if not DATABASE_URL:
        user = _users_memory.get(email)
        return user["subscription_status"] if user else "free"

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT subscription_status FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            return row["subscription_status"] if row else "free"


# In-memory stores for battles and wall entries
_battles_memory: dict[str, dict] = {}
_wall_entries_memory: dict[str, dict] = {}


def update_roast_voice(roast_id: str, script: str, audio_path: str) -> None:
    """Cache generated voice note script and audio path on roast."""
    if not DATABASE_URL:
        if roast_id in _memory_store:
            _memory_store[roast_id]["voice_script"] = script
            _memory_store[roast_id]["voice_audio_path"] = audio_path
        return

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE roasts
                SET voice_script = %s, voice_audio_path = %s
                WHERE id = %s
                """,
                (script, audio_path, roast_id),
            )
        conn.commit()


def save_battle(
    *,
    fighter_1_score: int,
    fighter_1_band: str,
    fighter_1_verdict: str,
    fighter_1_issues: list,
    fighter_1_strengths: list,
    fighter_2_score: int,
    fighter_2_band: str,
    fighter_2_verdict: str,
    fighter_2_issues: list,
    fighter_2_strengths: list,
    winner: str,
    margin: str,
    verdict: str,
    fighter_1_best_line: str,
    fighter_2_best_line: str,
    device_fingerprint: Optional[str] = None,
) -> str:
    """Save a comparative battle result."""
    battle_id = str(uuid4())
    now_utc = datetime.now(timezone.utc)
    expires_at = (now_utc + timedelta(days=ANONYMOUS_ROAST_EXPIRY_DAYS)).isoformat()

    data = {
        "id": battle_id,
        "fighter_1_score": fighter_1_score,
        "fighter_1_band": fighter_1_band,
        "fighter_1_verdict": fighter_1_verdict,
        "fighter_1_issues": fighter_1_issues,
        "fighter_1_strengths": fighter_1_strengths,
        "fighter_2_score": fighter_2_score,
        "fighter_2_band": fighter_2_band,
        "fighter_2_verdict": fighter_2_verdict,
        "fighter_2_issues": fighter_2_issues,
        "fighter_2_strengths": fighter_2_strengths,
        "winner": winner,
        "margin": margin,
        "verdict": verdict,
        "fighter_1_best_line": fighter_1_best_line,
        "fighter_2_best_line": fighter_2_best_line,
        "device_fingerprint": device_fingerprint,
        "created_at": now_utc.isoformat(),
        "expires_at": expires_at,
    }

    if not DATABASE_URL:
        _battles_memory[battle_id] = data
        return battle_id

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO battles
                  (id, fighter_1_score, fighter_1_band, fighter_1_verdict, fighter_1_issues, fighter_1_strengths,
                   fighter_2_score, fighter_2_band, fighter_2_verdict, fighter_2_issues, fighter_2_strengths,
                   winner, margin, verdict, fighter_1_best_line, fighter_2_best_line, device_fingerprint, expires_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    battle_id,
                    fighter_1_score,
                    fighter_1_band,
                    fighter_1_verdict,
                    json.dumps(fighter_1_issues),
                    json.dumps(fighter_1_strengths),
                    fighter_2_score,
                    fighter_2_band,
                    fighter_2_verdict,
                    json.dumps(fighter_2_issues),
                    json.dumps(fighter_2_strengths),
                    winner,
                    margin,
                    verdict,
                    fighter_1_best_line,
                    fighter_2_best_line,
                    device_fingerprint,
                    expires_at,
                ),
            )
        conn.commit()
    return battle_id


def get_battle(battle_id: str) -> Optional[dict]:
    """Retrieve battle details by ID."""
    now_utc = datetime.now(timezone.utc).isoformat()
    if not DATABASE_URL:
        b = _battles_memory.get(battle_id)
        if not b:
            return None
        if b.get("expires_at") and b["expires_at"] < now_utc:
            del _battles_memory[battle_id]
            return None
        return b

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM battles
                WHERE id = %s
                  AND (expires_at IS NULL OR expires_at > now())
                """,
                (battle_id,),
            )
            row = cur.fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Wall of Shame / Wall of Fame Helpers
# ---------------------------------------------------------------------------

def save_wall_entry(
    *,
    roast_id: Optional[str],
    entry_type: str,
    score: int,
    band: str,
    one_line_verdict: str,
    top_roast_lines: list[str],
    device_fingerprint: Optional[str] = None,
) -> str:
    """Save an anonymized public wall entry."""
    entry_id = str(uuid4())
    now_utc = datetime.now(timezone.utc).isoformat()

    entry = {
        "id": entry_id,
        "roast_id": roast_id,
        "type": entry_type,
        "score": score,
        "band": band,
        "one_line_verdict": one_line_verdict,
        "top_roast_lines": top_roast_lines,
        "flag_count": 0,
        "hidden": False,
        "device_fingerprint": device_fingerprint,
        "created_at": now_utc,
    }

    if not DATABASE_URL:
        _wall_entries_memory[entry_id] = entry
        return entry_id

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO wall_entries
                  (id, roast_id, type, score, band, one_line_verdict, top_roast_lines, device_fingerprint)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    entry_id,
                    roast_id,
                    entry_type,
                    score,
                    band,
                    one_line_verdict,
                    json.dumps(top_roast_lines),
                    device_fingerprint,
                ),
            )
        conn.commit()
    return entry_id


def get_wall_entries(
    entry_type: str = "shame",
    sort_by: str = "recent",
    page: int = 1,
    limit: int = 20,
) -> dict:
    """Fetch paginated, unhidden public wall entries."""
    offset = max(0, (page - 1) * limit)

    if not DATABASE_URL:
        entries = [
            v for v in _wall_entries_memory.values()
            if v["type"] == entry_type and not v.get("hidden", False)
        ]
        if sort_by == "score":
            # For shame: lowest score first; for fame: highest score first
            reverse = (entry_type == "fame")
            entries.sort(key=lambda x: x["score"], reverse=reverse)
        else:
            entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        total = len(entries)
        items = entries[offset : offset + limit]
        return {
            "items": items,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1,
        }

    with _get_conn() as conn:
        with conn.cursor() as cur:
            order_clause = "created_at DESC"
            if sort_by == "score":
                order_clause = "score DESC" if entry_type == "fame" else "score ASC"

            cur.execute(
                f"""
                SELECT * FROM wall_entries
                WHERE type = %s AND hidden = FALSE
                ORDER BY {order_clause}
                LIMIT %s OFFSET %s
                """,
                (entry_type, limit, offset),
            )
            rows = cur.fetchall()

            cur.execute(
                "SELECT COUNT(*) as count FROM wall_entries WHERE type = %s AND hidden = FALSE",
                (entry_type,),
            )
            total = cur.fetchone()["count"]

    items = []
    for r in rows:
        d = dict(r)
        if isinstance(d.get("top_roast_lines"), str):
            try:
                d["top_roast_lines"] = json.loads(d["top_roast_lines"])
            except Exception:
                d["top_roast_lines"] = []
        items.append(d)

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit if total > 0 else 1,
    }


def flag_wall_entry(entry_id: str) -> dict:
    """Flag a public wall entry. Auto-hides if flag count >= 3."""
    if not DATABASE_URL:
        entry = _wall_entries_memory.get(entry_id)
        if not entry:
            return {"found": False, "hidden": False}
        entry["flag_count"] = entry.get("flag_count", 0) + 1
        if entry["flag_count"] >= 3:
            entry["hidden"] = True
        return {"found": True, "flag_count": entry["flag_count"], "hidden": entry["hidden"]}

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE wall_entries
                SET flag_count = flag_count + 1,
                    hidden = CASE WHEN flag_count + 1 >= 3 THEN TRUE ELSE hidden END
                WHERE id = %s
                RETURNING flag_count, hidden
                """,
                (entry_id,),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        return {"found": False, "hidden": False}
    return {"found": True, "flag_count": row["flag_count"], "hidden": row["hidden"]}


def hide_wall_entry(entry_id: str, hidden: bool = True) -> bool:
    """Admin moderation tool to hide or unhide a wall entry."""
    if not DATABASE_URL:
        if entry_id in _wall_entries_memory:
            _wall_entries_memory[entry_id]["hidden"] = hidden
            return True
        return False

    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE wall_entries SET hidden = %s WHERE id = %s RETURNING id",
                (hidden, entry_id),
            )
            row = cur.fetchone()
        conn.commit()
    return bool(row)


VALID_REACTION_EMOJIS = {"laugh", "fire", "skull", "eyes"}


def get_roast_reactions(roast_id: str) -> dict[str, int]:
    """Retrieve emoji reactions counts for a given roast_id."""
    base = {"laugh": 0, "fire": 0, "skull": 0, "eyes": 0}
    if not DATABASE_URL:
        mem = _reactions_memory.get(roast_id, {})
        for k, v in mem.items():
            if k in base:
                base[k] = v
        return base

    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT emoji, count FROM roast_reactions WHERE roast_id = %s", (roast_id,))
                rows = cur.fetchall()
                for r in rows:
                    if r["emoji"] in base:
                        base[r["emoji"]] = r["count"]
                return base
    except Exception as e:
        print(f"[WARN] Error fetching roast reactions: {e}")
        return base


def add_roast_reaction(roast_id: str, emoji: str) -> dict[str, int]:
    """Increment emoji reaction count for a roast and return updated counts."""
    if emoji not in VALID_REACTION_EMOJIS:
        return get_roast_reactions(roast_id)

    if not DATABASE_URL:
        if roast_id not in _reactions_memory:
            _reactions_memory[roast_id] = {"laugh": 0, "fire": 0, "skull": 0, "eyes": 0}
        _reactions_memory[roast_id][emoji] = _reactions_memory[roast_id].get(emoji, 0) + 1
        return dict(_reactions_memory[roast_id])

    try:
        with _get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO roast_reactions (roast_id, emoji, count)
                    VALUES (%s, %s, 1)
                    ON CONFLICT (roast_id, emoji)
                    DO UPDATE SET count = roast_reactions.count + 1
                    """,
                    (roast_id, emoji),
                )
            conn.commit()
        return get_roast_reactions(roast_id)
    except Exception as e:
        print(f"[WARN] Error updating roast reaction: {e}")
        return get_roast_reactions(roast_id)


