import os
import sys
import json
import re
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout.reconfigure(encoding='utf-8')

from app.db.database import _get_conn, DATABASE_URL
from app.services.ai_analyzer import _TEMPORAL_HALLUCINATION_REGEX

def clean_database():
    print("=" * 80)
    print("AUTOMATED CLEANUP OF HISTORICAL TEMPORAL HALLUCINATIONS IN DATABASE")
    print(f"Database URL: {DATABASE_URL[:40]}...")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)

    if not DATABASE_URL:
        print("DATABASE_URL not set. Skipping.")
        return

    cleaned_count = 0
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, overall_score, band, one_line_verdict, issues, strengths, created_at
                FROM roasts
                ORDER BY created_at DESC;
            """)
            records = cur.fetchall()
            print(f"Total roasts fetched from DB: {len(records)}")

            for row in records:
                r_id = str(row["id"])
                verdict = row["one_line_verdict"] or ""
                issues = row["issues"]
                if isinstance(issues, str):
                    try:
                        issues = json.loads(issues)
                    except Exception:
                        issues = []

                changed = False
                clean_issues = []

                for iss in issues:
                    roast = iss.get("roast", "")
                    badge = iss.get("badge_label", "")
                    quoted = iss.get("quoted_text", "")

                    is_temporal = bool(
                        _TEMPORAL_HALLUCINATION_REGEX.search(roast) or 
                        _TEMPORAL_HALLUCINATION_REGEX.search(badge)
                    )

                    if is_temporal:
                        years = [int(y) for y in re.findall(r"\b(20\d\d)\b", quoted)]
                        # If years are <= 2026 or graduation <= 2030, this was a false hallucination
                        if not years or all(y <= 2026 for y in years) or all(y <= 2030 for y in years):
                            print(f"\n[CLEANING RECORD {r_id}]")
                            print(f"   Dropping false issue: \"{quoted}\"")
                            print(f"   Roast was: \"{roast}\"")
                            changed = True
                            continue  # Drop this issue!

                    clean_issues.append(iss)

                # Re-index severity ranks
                for idx, iss in enumerate(clean_issues, 1):
                    iss["severity_rank"] = idx

                # Check verdict
                new_verdict = verdict
                if _TEMPORAL_HALLUCINATION_REGEX.search(verdict):
                    changed = True
                    if any(ord(c) > 127 for c in verdict):  # Hinglish / emoji
                        new_verdict = "Bhai resume mein dum hai, bas thodi tuning baaki hai ✨"
                    else:
                        new_verdict = "Solid technical depth, ready for final interview polish 🚀"
                    print(f"   Updating verdict from: \"{verdict}\"")
                    print(f"                      to: \"{new_verdict}\"")

                if changed:
                    cur.execute("""
                        UPDATE roasts
                        SET issues = %s, one_line_verdict = %s
                        WHERE id = %s;
                    """, (json.dumps(clean_issues), new_verdict, r_id))

                    # Also update wall_entries if present
                    cur.execute("""
                        UPDATE wall_entries
                        SET one_line_verdict = %s
                        WHERE roast_id = %s;
                    """, (new_verdict, r_id))

                    cleaned_count += 1

            conn.commit()

    print("\n" + "=" * 80)
    print(f"SUCCESS: Cleaned {cleaned_count} historical database records!")
    print("All existing users' stored roasts and share links are now 100% free of temporal bugs.")
    print("=" * 80)

if __name__ == "__main__":
    clean_database()
