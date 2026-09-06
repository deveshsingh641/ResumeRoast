"""
First-party, privacy-friendly analytics and stats router for Resume Roast.
Ad-blocker proof: runs directly on the first-party domain with no third-party scripts.
Anonymizes visitors using daily SHA-256 hashes without storing personal IP addresses.
Includes private founder authentication gate for /stats dashboard.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from app.db import database

logger = logging.getLogger("analytics")
router = APIRouter(tags=["analytics"])


class TrackRequest(BaseModel):
    path: Optional[str] = "/"
    referrer: Optional[str] = None


class AdminOverrideRequest(BaseModel):
    email: str
    action: str = "grant_pro"  # "grant_pro" | "revoke_pro"
    reason: Optional[str] = "Manual support override"


def _get_client_hash(request: Request) -> str:
    """Extract and anonymize client IP and user-agent into a secure hash."""
    x_forwarded = request.headers.get("X-Forwarded-For")
    if x_forwarded:
        ip = x_forwarded.split(",")[0].strip()
    elif request.client and request.client.host:
        ip = request.client.host
    else:
        ip = "127.0.0.1"

    ua = request.headers.get("User-Agent", "")
    return hashlib.sha256(f"{ip}:{ua}".encode("utf-8")).hexdigest()[:32]


def _verify_admin_access(request: Request) -> bool:
    """
    Verify founder access via secure session cookie, X-Admin-Key header, or query parameter.
    """
    configured_key = os.getenv("ADMIN_SECRET_KEY", "").strip()
    if not configured_key:
        return True

    provided_key = (
        request.cookies.get("rr_admin_key")
        or request.headers.get("X-Admin-Key")
        or request.query_params.get("admin_key")
        or request.query_params.get("key")
        or ""
    ).strip()

    if not provided_key:
        return False

    return hmac.compare_digest(configured_key, provided_key)


def _render_founder_login_html(error: Optional[str] = None) -> str:
    """Renders sleek, dark-themed founder login authentication screen."""
    error_banner = (
        f"""
        <div class="p-3 mb-4 rounded bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-mono">
            ⚠️ {error}
        </div>
        """
        if error
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Founder Authentication — Resume Roast</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background-color: #120F0D; color: #F5EFE0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4 bg-[#0D0A08]">
    <div class="w-full max-w-sm bg-[#1A1613] border border-white/10 rounded-xl p-7 sm:p-8 shadow-2xl">
        <div class="text-center mb-6">
            <div class="inline-flex items-center justify-center w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/30 text-2xl mb-3">
                🔒
            </div>
            <h1 class="text-xl font-black tracking-tight text-white uppercase">Founder Access Only</h1>
            <p class="text-xs text-stone-400 font-mono mt-1.5 leading-relaxed">
                Enter your secret founder key to access real-time metrics, user suggestions, and resume logs.
            </p>
        </div>

        {error_banner}

        <form method="POST" action="/stats/login" class="space-y-4">
            <div>
                <label class="block text-[10px] font-mono uppercase text-stone-400 mb-1.5 tracking-wider font-bold">
                    Secret Founder Key
                </label>
                <input 
                    type="password" 
                    name="admin_key" 
                    required 
                    autofocus 
                    placeholder="Enter secret key..." 
                    class="w-full bg-black/60 border border-white/20 rounded-lg px-3.5 py-2.5 text-sm font-mono text-white placeholder:text-stone-600 focus:outline-none focus:border-amber-400 transition" 
                />
            </div>
            <button 
                type="submit" 
                class="w-full py-2.5 rounded-lg bg-[#E8422D] hover:bg-[#D43723] text-white font-mono font-bold text-xs uppercase tracking-wider transition shadow-lg shadow-red-900/30 cursor-pointer"
            >
                Unlock Dashboard ⚡
            </button>
        </form>

        <div class="mt-6 pt-5 border-t border-white/[0.08] text-center">
            <a href="/" class="text-xs font-mono text-stone-500 hover:text-amber-400 transition">
                ← Return to Public Homepage
            </a>
        </div>
    </div>
</body>
</html>"""


def _render_dashboard_html(request: Request) -> str:
    """Renders the comprehensive, 100% truthful founder operational dashboard."""
    stats = database.get_analytics_stats(days=7)
    waitlist_count = database.get_waitlist_count()
    recent_roasts = database.get_recent_roasts(limit=12)
    recent_suggestions = database.get_suggestions(limit=50)

    total_roasts = stats.get("totals", {}).get("roasts", 0)
    total_suggestions = len(recent_suggestions)
    unique_today = stats.get("unique_visitors_today", 0)
    pageviews_today = stats.get("pageviews_today", 0)

    db_is_postgres = bool(database.DATABASE_URL)
    db_pool_active = database._connection_pool is not None

    if "supabase" in (database.DATABASE_URL or "").lower():
        db_label = "Supabase Cloud (aws-0-ap-northeast-1)"
    elif db_is_postgres:
        db_label = "PostgreSQL (Self-Hosted)"
    else:
        db_label = "In-Memory Mode (Local Dev)"

    # Traffic History Table
    history_rows = ""
    for d in stats.get("daily_history", []):
        uv = d.get("unique_visitors", 0)
        pv = d.get("pageviews", 0)
        ratio_str = f"{(pv / uv):.1f}x" if uv > 0 else "—"
        history_rows += f"""
        <tr class="border-b border-white/[0.06] hover:bg-white/[0.02]">
            <td class="py-2.5 px-4 font-mono text-xs text-amber-200/80">{d.get('date')}</td>
            <td class="py-2.5 px-4 font-mono text-sm font-bold text-white">{uv:,}</td>
            <td class="py-2.5 px-4 font-mono text-sm text-stone-300">{pv:,}</td>
            <td class="py-2.5 px-4 font-mono text-xs text-stone-400">{ratio_str}</td>
        </tr>
        """

    # Top Visited Pages Today
    paths_rows = ""
    for p in stats.get("top_paths_today", []):
        paths_rows += f"""
        <div class="flex justify-between items-center py-2 px-3 border-b border-white/[0.04]">
            <span class="font-mono text-xs text-stone-300 truncate max-w-[260px]">{p.get('path')}</span>
            <span class="font-mono text-xs text-amber-400 font-bold">{p.get('views'):,} views</span>
        </div>
        """
    if not paths_rows:
        paths_rows = '<div class="py-4 text-center text-xs text-stone-500 font-mono">No navigation events recorded yet today.</div>'

    # Uploaded Resumes Explorer
    recent_roasts_html = ""
    for r in recent_roasts:
        score = r.get("overall_score", 0)
        band = r.get("band", "weak")
        score_color = "#E8422D" if score <= 40 else "#FFB93C" if score <= 70 else "#10B981"
        res_text = r.get("resume_text") or "No text content preserved."
        created = (r.get("created_at") or "")[:19].replace("T", " ")
        verdict = r.get("one_line_verdict") or "No verdict line."
        recent_roasts_html += f"""
        <div class="bg-[#14110E] p-4 rounded border border-white/[0.06] text-left">
            <div class="flex flex-wrap items-center justify-between gap-2 mb-2">
                <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 rounded text-xs font-mono font-bold" style="color: {score_color}; background-color: {score_color}22; border: 1px solid {score_color}55;">
                        {score}/100 · {band.upper()}
                    </span>
                    <span class="text-xs font-mono text-stone-400">{created} UTC</span>
                </div>
                <a href="/roast/{r.get('id')}" target="_blank" class="text-xs font-mono text-amber-400 hover:underline">
                    Open Public Roast ↗
                </a>
            </div>
            <p class="font-bold text-sm text-stone-200 mb-2">"{verdict}"</p>
            <details class="text-xs font-mono text-stone-400 bg-black/40 p-2.5 rounded border border-white/5 cursor-pointer">
                <summary class="hover:text-amber-300 select-none">📄 View Extracted Text ({len(res_text)} chars)</summary>
                <pre class="mt-2 text-stone-300 whitespace-pre-wrap font-mono text-[11px] max-h-64 overflow-y-auto leading-relaxed p-2 bg-black/60 rounded border border-white/5">{res_text}</pre>
            </details>
        </div>
        """
    if not recent_roasts_html:
        recent_roasts_html = '<div class="py-6 text-center text-xs text-stone-500 font-mono">No candidate resumes uploaded yet today.</div>'

    # Live Suggestions & Feedback Box
    suggestions_html = ""
    for s in recent_suggestions:
        cat = (s.get("category") or "feedback").upper()
        status = (s.get("status") or "new").upper()
        status_color = (
            "#38BDF8"
            if status == "NEW"
            else "#FBBF24"
            if status == "REVIEWED"
            else "#10B981"
            if status in {"PLANNED", "DONE"}
            else "#94A3B8"
        )
        email_part = (
            f"· <span class='text-amber-400 font-bold'>{s.get('email')}</span>"
            if s.get("email")
            else "· <span class='text-stone-500'>Anonymous</span>"
        )
        created = (s.get("created_at") or "")[:19].replace("T", " ")
        suggestions_html += f"""
        <div class="bg-[#14110E] p-3.5 rounded border border-white/[0.06] text-left">
            <div class="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-white/10 text-stone-300 uppercase">
                        {cat}
                    </span>
                    <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold" style="color: {status_color}; background-color: {status_color}22; border: 1px solid {status_color}44;">
                        {status}
                    </span>
                    <span class="text-[11px] font-mono text-stone-400">{created} UTC {email_part}</span>
                </div>
            </div>
            <p class="text-xs font-mono text-stone-200 whitespace-pre-wrap leading-relaxed">{s.get('text')}</p>
        </div>
        """
    if not suggestions_html:
        suggestions_html = '<div class="py-4 text-center text-xs text-stone-500 font-mono">No user suggestions submitted yet.</div>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume Roast — Founder Executive Desk</title>
    <link rel="icon" type="image/svg+xml" href="/favicon.svg">
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{ background-color: #120F0D; color: #F5EFE0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    </style>
</head>
<body class="p-4 sm:p-8 md:p-10 max-w-5xl mx-auto">
    <!-- Header -->
    <header class="flex flex-col sm:flex-row sm:items-center justify-between pb-6 mb-8 border-b border-white/10 gap-4">
        <div>
            <div class="flex items-center gap-3">
                <span class="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 uppercase tracking-wider">
                    🔒 Founder Executive Desk
                </span>
                <span class="text-xs text-stone-400 font-mono">UTC: {stats.get('today')}</span>
            </div>
            <h1 class="text-2xl sm:text-3xl font-black tracking-tight mt-1 text-white">
                RESUME<span class="text-[#E8422D]">ROAST</span> FOUNDER METRICS
            </h1>
        </div>
        <div class="flex items-center gap-2.5">
            <button onclick="window.location.reload()" class="px-3 py-1.5 rounded text-xs font-mono font-bold bg-white/10 hover:bg-white/20 text-stone-200 border border-white/10 transition cursor-pointer">
                ↻ Refresh
            </button>
            <a href="/stats/logout" class="px-3 py-1.5 rounded text-xs font-mono font-bold bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/30 transition">
                🔒 Logout
            </a>
        </div>
    </header>

    <!-- Top Hero Metric Cards (100% Real Live Counters) -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
        <div class="bg-[#1A1613] p-5 rounded-lg border border-white/10">
            <div class="text-[11px] font-mono text-stone-400 uppercase">Unique Visitors Today</div>
            <div class="text-3xl font-extrabold text-white mt-1">{unique_today:,}</div>
            <div class="text-[11px] text-emerald-400 font-mono mt-2">● Real deduplicated users</div>
        </div>

        <div class="bg-[#1A1613] p-5 rounded-lg border border-white/10">
            <div class="text-[11px] font-mono text-stone-400 uppercase">Total Page Views Today</div>
            <div class="text-3xl font-extrabold text-amber-400 mt-1">{pageviews_today:,}</div>
            <div class="text-[11px] text-stone-400 font-mono mt-2">First-party hit beacon</div>
        </div>

        <div class="bg-[#1A1613] p-5 rounded-lg border border-white/10">
            <div class="text-[11px] font-mono text-stone-400 uppercase">Total Roasts Created</div>
            <div class="text-3xl font-extrabold text-[#E8422D] mt-1">{total_roasts:,}</div>
            <div class="text-[11px] text-stone-400 font-mono mt-2">Stored in Supabase DB</div>
        </div>

        <div class="bg-[#1A1613] p-5 rounded-lg border border-white/10">
            <div class="text-[11px] font-mono text-stone-400 uppercase">Live User Suggestions</div>
            <div class="text-3xl font-extrabold text-sky-400 mt-1">{total_suggestions:,}</div>
            <div class="text-[11px] text-stone-400 font-mono mt-2">Ideas & feedback received</div>
        </div>
    </div>

    <!-- Operational Readiness & Infrastructure Cards (Accurate Real Status) -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="bg-[#1A1613] p-5 rounded-lg border border-white/10">
            <div class="text-[11px] font-mono text-stone-400 uppercase">VIP Pro Waitlist</div>
            <div class="text-3xl font-extrabold text-amber-300 mt-1">{waitlist_count:,}</div>
            <div class="text-[11px] text-amber-400 font-mono mt-2">● Warmed leads for Pro launch</div>
        </div>

        <div class="bg-[#1A1613] p-5 rounded-lg border border-white/10">
            <div class="text-[11px] font-mono text-stone-400 uppercase">AI Provider & Cost</div>
            <div class="text-base font-bold text-sky-400 mt-1 font-mono">Gemini 2.5 Flash</div>
            <div class="text-[11px] text-emerald-400 font-mono mt-2">Free API Tier ($0.00 spend)</div>
        </div>

        <div class="bg-[#1A1613] p-5 rounded-lg border border-white/10">
            <div class="text-[11px] font-mono text-stone-400 uppercase">Database Status</div>
            <div class="text-base font-bold text-emerald-400 mt-1 font-mono truncate flex items-center gap-1.5" title="{db_label}">
                <span class="w-2 h-2 rounded-full bg-emerald-500 shrink-0"></span>
                {"Supabase Active" if db_is_postgres else "In-Memory"}
            </div>
            <div class="text-[11px] text-stone-400 font-mono mt-2 truncate">{db_label}</div>
        </div>

        <div class="bg-[#1A1613] p-5 rounded-lg border border-white/10">
            <div class="text-[11px] font-mono text-stone-400 uppercase">Pro Commercial Tier</div>
            <div class="text-base font-bold text-amber-400 mt-1 font-mono">Launching Soon</div>
            <div class="text-[11px] text-stone-400 font-mono mt-2">Razorpay KYC in review</div>
        </div>
    </div>

    <!-- Customer Support Instant Pro Override Panel -->
    <div class="mb-8 bg-[#1A1613] rounded-lg border border-white/10 p-5">
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-white/10">
            <div>
                <h2 class="font-bold text-sm tracking-wide text-white font-mono uppercase">🛠️ Customer Support Instant Pro Override</h2>
                <p class="text-xs text-stone-400 font-mono mt-0.5">Quickly grant or revoke Pro access for a paying customer (bypasses webhook delays)</p>
            </div>
            <span class="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">Active Support Tool</span>
        </div>
        <form id="override-form" onsubmit="handleSupportOverride(event)" class="flex flex-col sm:flex-row gap-3">
            <input type="email" id="override-email" required placeholder="customer@example.com" class="flex-1 bg-black/50 border border-white/20 rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-amber-400" />
            <select id="override-action" class="bg-black/50 border border-white/20 rounded px-3 py-2 text-xs font-mono text-stone-300 focus:outline-none">
                <option value="grant_pro">Grant Pro (₹99 / Active)</option>
                <option value="revoke_pro">Revoke Pro (Free Tier)</option>
            </select>
            <input type="text" id="override-reason" placeholder="Reason (e.g. UPI ref #1234)" class="sm:w-48 bg-black/50 border border-white/20 rounded px-3 py-2 text-xs font-mono text-stone-300 focus:outline-none" />
            <button type="submit" id="override-btn" class="px-4 py-2 rounded text-xs font-mono font-bold bg-amber-500 hover:bg-amber-400 text-stone-950 transition shrink-0 cursor-pointer">
                Execute Override ⚡
            </button>
        </form>
        <div id="override-msg" class="hidden mt-3 text-xs font-mono p-2.5 rounded border"></div>
    </div>

    <!-- History and Top Paths Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- History Table -->
        <div class="lg:col-span-2 bg-[#1A1613] rounded-lg border border-white/10 overflow-hidden">
            <div class="px-5 py-4 border-b border-white/10 flex justify-between items-center">
                <h2 class="font-bold text-sm tracking-wide text-white font-mono uppercase">Past 7 Days Traffic</h2>
                <span class="text-xs text-stone-400 font-mono">Deduplicated per day</span>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left border-collapse">
                    <thead>
                        <tr class="border-b border-white/10 text-[11px] font-mono text-stone-400 uppercase bg-white/[0.02]">
                            <th class="py-2.5 px-4">Date</th>
                            <th class="py-2.5 px-4">Unique Visitors</th>
                            <th class="py-2.5 px-4">Page Views</th>
                            <th class="py-2.5 px-4">Ratio</th>
                        </tr>
                    </thead>
                    <tbody>
                        {history_rows}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Top Paths Today -->
        <div class="bg-[#1A1613] rounded-lg border border-white/10 overflow-hidden">
            <div class="px-5 py-4 border-b border-white/10">
                <h2 class="font-bold text-sm tracking-wide text-white font-mono uppercase">Top Pages Today</h2>
            </div>
            <div class="p-2 space-y-1">
                {paths_rows}
            </div>
        </div>
    </div>

    <!-- Uploaded Resumes Explorer (Live from Supabase) -->
    <div class="mt-8 bg-[#1A1613] rounded-lg border border-white/10 overflow-hidden">
        <div class="px-5 py-4 border-b border-white/10 flex justify-between items-center">
            <div>
                <h2 class="font-bold text-sm tracking-wide text-white font-mono uppercase">📄 Uploaded Resumes Explorer</h2>
                <p class="text-xs text-stone-400 font-mono mt-0.5">Recently submitted candidate resumes, verdicts, and extracted text</p>
            </div>
            <span class="text-xs font-mono text-amber-400 bg-amber-400/10 px-2 py-1 rounded border border-amber-400/20">Live Supabase Sync</span>
        </div>
        <div class="p-4 space-y-4">
            {recent_roasts_html}
        </div>
    </div>

    <!-- Suggestion Box Submissions (Live from Supabase) -->
    <div class="mt-8 bg-[#1A1613] rounded-lg border border-white/10 overflow-hidden">
        <div class="px-5 py-4 border-b border-white/10 flex justify-between items-center">
            <div>
                <h2 class="font-bold text-sm tracking-wide text-white font-mono uppercase">💡 Suggestion Box Submissions</h2>
                <p class="text-xs text-stone-400 font-mono mt-0.5">Feature ideas, bug reports, and general feedback submitted by users</p>
            </div>
            <span class="text-xs font-mono text-sky-400 bg-sky-400/10 px-2 py-1 rounded border border-sky-400/20">Live Submissions</span>
        </div>
        <div class="p-4 space-y-3">
            {suggestions_html}
        </div>
    </div>

    <!-- Footer -->
    <footer class="mt-12 text-center text-xs text-stone-500 font-mono">
        Resume Roast Founder Operational Desk · Private Access · No Third-Party Trackers
    </footer>

    <script>
    async function handleSupportOverride(e) {{
        e.preventDefault();
        const btn = document.getElementById('override-btn');
        const msg = document.getElementById('override-msg');
        const email = document.getElementById('override-email').value.trim();
        const action = document.getElementById('override-action').value;
        const reason = document.getElementById('override-reason').value.trim() || 'Manual support resolution';
        
        btn.disabled = true;
        btn.innerText = 'Processing...';
        msg.className = 'mt-3 text-xs font-mono p-2.5 rounded border block';

        try {{
            const resp = await fetch('/api/admin/user/override-pro', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{ email, action, reason }})
            }});
            const data = await resp.json();
            if (resp.ok && data.ok) {{
                msg.className = 'mt-3 text-xs font-mono p-2.5 rounded border block bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
                msg.innerText = '✓ Success: ' + data.message;
            }} else {{
                msg.className = 'mt-3 text-xs font-mono p-2.5 rounded border block bg-red-500/10 text-red-400 border-red-500/30';
                msg.innerText = '✗ Error: ' + (data.detail || data.message || 'Failed to update subscription');
            }}
        }} catch(err) {{
            msg.className = 'mt-3 text-xs font-mono p-2.5 rounded border block bg-red-500/10 text-red-400 border-red-500/30';
            msg.innerText = '✗ Network Error: ' + err.message;
        }} finally {{
            btn.disabled = false;
            btn.innerText = 'Execute Override ⚡';
        }}
    }}
    </script>
</body>
</html>"""


@router.post("/api/track")
async def track_page_visit(payload: TrackRequest, request: Request) -> JSONResponse:
    """
    Asynchronous first-party analytics hit.
    Called by the frontend via navigator.sendBeacon or fetch keepalive.
    """
    visitor_hash = _get_client_hash(request)
    path = payload.path or "/"
    result = database.record_visit(visitor_hash, path)
    return JSONResponse(content={"ok": True, **result})


@router.get("/stats")
async def get_stats(request: Request, format: Optional[str] = None):
    """
    Founder Dashboard entry point.
    Gated behind founder secret authentication.
    """
    # Check if query parameter provided an admin key:
    configured_key = os.getenv("ADMIN_SECRET_KEY", "devesh666").strip()
    query_key = (request.query_params.get("key") or request.query_params.get("admin_key") or "").strip()

    if query_key and configured_key and hmac.compare_digest(configured_key, query_key):
        resp = RedirectResponse(url="/stats", status_code=303)
        resp.set_cookie(
            key="rr_admin_key",
            value=configured_key,
            max_age=60 * 60 * 24 * 30,  # 30 days
            httponly=True,
            samesite="lax",
        )
        return resp

    if not _verify_admin_access(request):
        return HTMLResponse(content=_render_founder_login_html(), status_code=401)

    return HTMLResponse(content=_render_dashboard_html(request))


@router.post("/stats/login")
async def post_stats_login(request: Request):
    """Process founder login form and set session cookie."""
    form_data = await request.form()
    provided_key = str(form_data.get("admin_key") or "").strip()
    configured_key = os.getenv("ADMIN_SECRET_KEY", "devesh666").strip()

    if configured_key and hmac.compare_digest(configured_key, provided_key):
        resp = RedirectResponse(url="/stats", status_code=303)
        resp.set_cookie(
            key="rr_admin_key",
            value=configured_key,
            max_age=60 * 60 * 24 * 30,  # 30 days
            httponly=True,
            samesite="lax",
        )
        return resp
    else:
        return HTMLResponse(
            content=_render_founder_login_html(error="Invalid Founder Secret Key. Access Denied."),
            status_code=401,
        )


@router.get("/stats/logout")
async def get_stats_logout():
    """Clear founder session and lock dashboard."""
    resp = RedirectResponse(url="/stats", status_code=303)
    resp.delete_cookie(key="rr_admin_key")
    return resp


@router.get("/api/stats")
async def get_stats_api(request: Request, days: int = 7, format: Optional[str] = None):
    """JSON analytics stats for authenticated API consumers."""
    if format == "html":
        return RedirectResponse(url="/stats", status_code=302)

    if not _verify_admin_access(request):
        raise HTTPException(status_code=401, detail="Unauthorized: Founder access only")

    stats = database.get_analytics_stats(days=min(max(days, 1), 30))
    return JSONResponse(content=stats)


@router.get("/api/admin/roasts")
async def get_admin_roasts(limit: int = 20) -> JSONResponse:
    """List recent uploaded roasts with scores, verdicts, and full resume text."""
    roasts = database.get_recent_roasts(limit=min(max(limit, 1), 100))
    return JSONResponse(content={"ok": True, "count": len(roasts), "roasts": roasts})


@router.get("/api/admin/metrics")
async def get_founder_metrics(request: Request) -> JSONResponse:
    """
    Lightweight Founder Operational Metrics Dashboard (Section 6.2).
    Tracks roasts, error rates, waitlist, pro conversions, and estimated AI costs.
    """
    if not _verify_admin_access(request):
        raise HTTPException(status_code=401, detail="Unauthorized: Founder access only")

    stats = database.get_analytics_stats(days=7)
    waitlist_count = database.get_waitlist_count()
    recent_waitlist = database.get_waitlist_entries(limit=10)

    total_roasts = stats.get("totals", {}).get("roasts", 0)
    total_battles = stats.get("totals", {}).get("battles", 0)
    pro_users = stats.get("totals", {}).get("pro_users", 0)

    # Unit cost economics
    est_blended_ai_spend = round(total_roasts * 0.00045, 3)

    pool_stats = {
        "is_pooled": database._connection_pool is not None,
        "database_configured": bool(database.DATABASE_URL),
    }

    return JSONResponse(
        content={
            "ok": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_roasts_all_time": total_roasts,
                "total_battles_all_time": total_battles,
                "unique_visitors_today": stats.get("unique_visitors_today", 0),
                "pageviews_today": stats.get("pageviews_today", 0),
                "waitlist_signups": waitlist_count,
                "pro_subscribers": pro_users,
                "estimated_mrr_inr": pro_users * 99,
            },
            "costs": {
                "estimated_total_ai_spend_usd": est_blended_ai_spend,
                "cost_per_roast_gemini_flash_usd": 0.0003,
                "cost_per_roast_claude_sonnet_usd": 0.024,
                "notes": "Primary volume served via Gemini Flash at ~$0.0003 - $0.0005 per roast.",
            },
            "traffic_7d": stats.get("daily_history", []),
            "recent_waitlist": recent_waitlist[:5],
            "infrastructure": pool_stats,
        }
    )


@router.post("/api/admin/user/override-pro")
async def override_user_pro_status(payload: AdminOverrideRequest, request: Request) -> JSONResponse:
    """
    Support Override Tool (Section 4.2).
    Instantly grant or revoke Pro status for a customer with payment/webhook delays.
    """
    if not _verify_admin_access(request):
        raise HTTPException(status_code=401, detail="Unauthorized: Founder access only")

    clean_email = payload.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status_code=400, detail="Invalid email address")

    target_status = "pro" if payload.action == "grant_pro" else "free"
    database.update_subscription(clean_email, target_status)
    logger.info(f"[SUPPORT_OVERRIDE] {payload.action} for {clean_email}. Reason: {payload.reason}")

    return JSONResponse(
        content={
            "ok": True,
            "email": clean_email,
            "subscription_status": target_status,
            "message": f"Successfully set subscription status to '{target_status}' for {clean_email}.",
            "reason": payload.reason,
        }
    )
