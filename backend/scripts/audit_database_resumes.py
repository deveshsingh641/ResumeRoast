import os
import sys
import json
import re
from datetime import datetime

# Set up backend path and utf-8 output
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.database import _get_conn, DATABASE_URL, _memory_store
from app.services.ai_analyzer import _TEMPORAL_HALLUCINATION_REGEX

def audit_database():
    print("=" * 80)
    print("AUDITING ALL UPLOADED RESUMES IN DATABASE")
    print(f"Database Mode: {'PostgreSQL / Supabase' if DATABASE_URL else 'In-Memory Store'}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    rows = []
    if DATABASE_URL:
        try:
            with _get_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, overall_score, band, one_line_verdict, issues, strengths, 
                               experience_header_line, resume_text, created_at 
                        FROM roasts 
                        ORDER BY created_at DESC;
                    """)
                    records = cur.fetchall()
                    for r in records:
                        rows.append(dict(r))
            print(f"Successfully connected to PostgreSQL. Found {len(rows)} roast record(s).")
        except Exception as e:
            print(f"Error reading from PostgreSQL database: {e}")
            print("Falling back to inspecting in-memory store...")

    if not rows and _memory_store:
        print(f"Inspecting in-memory store ({len(_memory_store)} records)...")
        for k, v in _memory_store.items():
            rows.append(v)

    if not rows:
        print("No roast records found in database or memory store.")
        return

    flawed_records = []
    clean_records = 0

    for idx, r in enumerate(rows, 1):
        roast_id = str(r.get("id"))
        score = r.get("overall_score")
        band = r.get("band")
        verdict = r.get("one_line_verdict", "")
        issues = r.get("issues", [])
        if isinstance(issues, str):
            try:
                issues = json.loads(issues)
            except Exception:
                issues = []
        strengths = r.get("strengths", [])
        if isinstance(strengths, str):
            try:
                strengths = json.loads(strengths)
            except Exception:
                strengths = []
        resume_text = r.get("resume_text", "")
        created_at = str(r.get("created_at", ""))

        record_flaws = []

        # 1. Check verdict for temporal hallucination
        if _TEMPORAL_HALLUCINATION_REGEX.search(verdict):
            record_flaws.append({
                "type": "TEMPORAL_VERDICT_HALLUCINATION",
                "detail": f"Verdict: '{verdict}'"
            })

        # 2. Check each issue
        for i_idx, iss in enumerate(issues, 1):
            roast = iss.get("roast", "")
            badge = iss.get("badge_label", "")
            quoted = iss.get("quoted_text", "")
            cat = iss.get("category", "")

            # Temporal hallucination check
            if _TEMPORAL_HALLUCINATION_REGEX.search(roast) or _TEMPORAL_HALLUCINATION_REGEX.search(badge):
                record_flaws.append({
                    "type": "TEMPORAL_ISSUE_HALLUCINATION",
                    "detail": f"Issue [{i_idx}] Quoted: '{quoted}' | Roast: '{roast}'"
                })

            # False no-metrics check
            if cat == "no-metrics":
                has_num = bool(re.search(r"\d", quoted) or "%" in quoted)
                if has_num:
                    record_flaws.append({
                        "type": "FALSE_NO_METRICS",
                        "detail": f"Issue [{i_idx}] Quoted: '{quoted}' contains numbers/percentages."
                    })

            # Quoted text existence in resume_text
            if resume_text and quoted:
                norm_q = " ".join(quoted.split())
                norm_r = " ".join(resume_text.split())
                if norm_q not in norm_r:
                    record_flaws.append({
                        "type": "QUOTED_TEXT_NOT_IN_RESUME",
                        "detail": f"Issue [{i_idx}] Quoted: '{quoted}' not found in stored resume_text."
                    })

        # 3. Print report for this record
        print(f"\n[{idx}/{len(rows)}] Roast ID: {roast_id} | Score: {score} ({band}) | Created: {created_at[:19]}")
        print(f"      Verdict: \"{verdict}\"")
        print(f"      Issues count: {len(issues)} | Strengths count: {len(strengths)}")

        if record_flaws:
            print(f"      [FLAGGED] Found {len(record_flaws)} potential issue(s):")
            for f in record_flaws:
                print(f"         - [{f['type']}] {f['detail']}")
            flawed_records.append({
                "id": roast_id,
                "created_at": created_at,
                "verdict": verdict,
                "flaws": record_flaws
            })
        else:
            print("      [CLEAN] No hallucinations or false critiques detected.")
            clean_records += 1

    print("\n" + "=" * 80)
    print("DATABASE AUDIT SUMMARY")
    print("=" * 80)
    print(f"Total Roasts Inspected: {len(rows)}")
    print(f"Completely Clean:       {clean_records}")
    print(f"Flagged Records:        {len(flawed_records)}")
    print("=" * 80)

    if flawed_records:
        print("\nFlagged Records Summary:")
        for fr in flawed_records:
            print(f"- ID: {fr['id']} (Date: {fr['created_at'][:19]})")
            for fl in fr["flaws"]:
                print(f"    * {fl['type']}: {fl['detail']}")
    else:
        print("All records in database are clean and accurate!")

if __name__ == "__main__":
    audit_database()
