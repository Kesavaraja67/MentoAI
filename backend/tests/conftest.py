"""
conftest.py — pytest configuration for all backend tests.

FalkorDB integration tests are skipped with a clear message when no container
is reachable (so the CI runner without Docker still gets a clean run report).
"""
import pytest
from falkordb import FalkorDB
from app.config import get_settings


def _falkordb_reachable() -> bool:
    try:
        s = get_settings()
        db = FalkorDB(host=s.falkordb_host, port=s.falkordb_port)
        db.select_graph("_conftest_ping").query("RETURN 1")
        return True
    except Exception:
        return False


requires_falkordb = pytest.mark.skipif(
    not _falkordb_reachable(),
    reason="FalkorDB not reachable. Start the container first: docker compose up -d falkordb",
)
