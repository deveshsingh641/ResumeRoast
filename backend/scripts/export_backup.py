"""
Database Backup & Export Utility (Operational Readiness Part 5).
Exports snapshot of critical tables (users, roasts, pro_waitlist, battles, wall_entries)
into a structured, timestamped JSON file for disaster recovery and off-site archives.

Usage:
    python backend/scripts/export_backup.py
    python backend/scripts/export_backup.py --output-dir ./backups
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db import database


def main():
    parser = argparse.ArgumentParser(description="Resume Roast Disaster Recovery Backup Export")
    parser.add_argument(
        "--output-dir",
        default=str(backend_dir / "storage" / "backups"),
        help="Target folder for backup archives",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_filename = f"resumeroast_backup_{timestamp}.json"
    target_file = out_dir / backup_filename

    print("=" * 60)
    print("RESUME ROAST — DATABASE BACKUP EXPORTER")
    print(f"Timestamp   : {timestamp} UTC")
    print(f"Target File : {target_file}")
    print("=" * 60)

    backup_payload = {
        "metadata": {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "environment": os.getenv("ENVIRONMENT", "production"),
            "schema_version": "1.0",
        },
        "tables": {},
    }

    # Query tables safely
    if not database.DATABASE_URL:
        print("[INFO] Backing up in-memory storage...")
        backup_payload["tables"]["users"] = list(database._users_memory.values())
        backup_payload["tables"]["roasts"] = list(database._memory_store.values())
        backup_payload["tables"]["pro_waitlist"] = list(database._waitlist_memory.values())
        backup_payload["tables"]["battles"] = list(getattr(database, "_battles_memory", {}).values())
        backup_payload["tables"]["suggestions"] = list(database._suggestions_memory)
    else:
        print("[INFO] Connecting to primary PostgreSQL database...")
        table_names = ["users", "roasts", "pro_waitlist", "suggestions", "battles", "wall_entries"]
        with database._get_conn() as conn:
            with conn.cursor() as cur:
                for tbl in table_names:
                    try:
                        cur.execute(f"SELECT * FROM {tbl}")
                        rows = cur.fetchall()
                        clean_rows = []
                        for r in rows:
                            d = dict(r)
                            # Convert non-serializable types to strings
                            for k, v in d.items():
                                if hasattr(v, "isoformat"):
                                    d[k] = v.isoformat()
                                elif str(type(v)).find("UUID") != -1:
                                    d[k] = str(v)
                            clean_rows.append(d)
                        backup_payload["tables"][tbl] = clean_rows
                        print(f"  [OK] Exported {tbl:<15}: {len(clean_rows):>5} rows")
                    except Exception as err:
                        print(f"  [FAIL] Failed table {tbl}: {err}")
                        backup_payload["tables"][tbl] = []

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(backup_payload, f, indent=2, ensure_ascii=False)

    size_kb = target_file.stat().st_size / 1024
    print("\nBACKUP COMPLETED SUCCESSFULLY:")
    print(f"  Location  : {target_file}")
    print(f"  File Size : {size_kb:.1f} KB")
    print("=" * 60)


if __name__ == "__main__":
    main()
