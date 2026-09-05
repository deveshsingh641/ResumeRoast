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

from app.db import database
database.DATABASE_URL = ""


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


@pytest.fixture(autouse=True)
def ensure_db_isolated():
    """Guarantee that tests always operate strictly in-memory and clean state between tests."""
    _clear_all_memory()
    yield
    _clear_all_memory()
