import os
import sys
from pathlib import Path
import pytest

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# CRITICAL: Isolate automated tests completely from remote production database!
# This prevents test runs from polluting Supabase or inserting test data into the live Wall of Shame.
os.environ["DATABASE_URL"] = ""
os.environ["ADMIN_SECRET_KEY"] = ""
os.environ["HISTORICAL_ROASTS_OFFSET"] = "0"
os.environ["HISTORICAL_UNIQUE_OFFSET"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""

from app.db import database
database.DATABASE_URL = ""
database.HISTORICAL_ROASTS_OFFSET = 0
database.HISTORICAL_UNIQUE_OFFSET = 0


def _clear_all_memory():
    database.DATABASE_URL = ""
    if hasattr(database, "_wall_entries_memory"):
        database._wall_entries_memory.clear()
    if hasattr(database, "_roasts_memory"):
        database._roasts_memory.clear()
    if hasattr(database, "_memory_store"):
        database._memory_store.clear()
    if hasattr(database, "_usage_memory"):
        database._usage_memory.clear()
    if hasattr(database, "_dedup_cache"):
        database._dedup_cache.clear()


from app.services import admin_auth
from app.core.limiter import limiter
from app.routers import payment

# Disable slowapi request rate-limiting during pytest execution to prevent test suite throttling
limiter.enabled = False


@pytest.fixture(autouse=True)
def ensure_db_isolated():
    """Guarantee that tests always operate strictly in-memory and clean state between tests."""
    os.environ["ADMIN_SECRET_KEY"] = ""
    admin_auth._failed_attempts.clear()
    payment._processed_payments.clear()
    payment._active_orders_cache.clear()
    payment._order_email_map.clear()
    _clear_all_memory()
    yield
    os.environ["ADMIN_SECRET_KEY"] = ""
    admin_auth._failed_attempts.clear()
    payment._processed_payments.clear()
    payment._active_orders_cache.clear()
    payment._order_email_map.clear()
    _clear_all_memory()
