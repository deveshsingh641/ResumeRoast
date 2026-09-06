"""
CLI Utility for manual Pro subscription overrides (Support Scenario 4.2).
Run directly from terminal or cloud host shell to immediately resolve customer access issues.

Usage:
    python backend/scripts/manual_pro_override.py user@example.com
    python backend/scripts/manual_pro_override.py user@example.com --action revoke
"""
import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db import database


def main():
    parser = argparse.ArgumentParser(description="Manual Pro Subscription Support Tool")
    parser.add_argument("email", help="Customer email address")
    parser.add_argument(
        "--action",
        choices=["grant", "revoke", "check"],
        default="grant",
        help="Action to perform: grant (default), revoke, or check current status",
    )
    parser.add_argument("--reason", default="Customer Support Manual Resolution", help="Audit log note")
    args = parser.parse_args()

    clean_email = args.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        print(f"[ERROR] Invalid email address: '{args.email}'")
        sys.exit(1)

    database.init_db()

    if args.action == "check":
        status = database.get_user_subscription(clean_email)
        print(f"Customer: {clean_email}")
        print(f"Current Subscription Status: {status.upper()}")
        return

    target_status = "pro" if args.action == "grant" else "free"
    database.update_subscription(clean_email, target_status)
    new_status = database.get_user_subscription(clean_email)

    print("=" * 60)
    print("RESUME ROAST — CUSTOMER SUPPORT OVERRIDE COMPLETED")
    print(f"Customer Email : {clean_email}")
    print(f"Target Status  : {target_status.upper()}")
    print(f"Active Status  : {new_status.upper()}")
    print(f"Audit Note     : {args.reason}")
    print("=" * 60)


if __name__ == "__main__":
    main()
