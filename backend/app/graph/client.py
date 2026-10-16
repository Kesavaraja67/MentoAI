"""
graph/client.py — thin wrapper around the falkordb Python client.
Returns a single FalkorDB connection shared per process (sync, thread-safe for
FastAPI sync endpoints). Each graph is accessed by name.
"""
from __future__ import annotations

import threading
from typing import Any

import falkordb

from app.config import get_settings

_lock = threading.Lock()
_connection: falkordb.FalkorDB | None = None


def get_db() -> falkordb.FalkorDB:
    """Return the shared FalkorDB connection, creating it once."""
    global _connection
    if _connection is None:
        with _lock:
            if _connection is None:
                s = get_settings()
                _connection = falkordb.FalkorDB(host=s.falkordb_host, port=s.falkordb_port)
    return _connection


def get_graph(name: str) -> falkordb.Graph:
    """Return a named graph handle. Creating it is a no-op if it exists."""
    return get_db().select_graph(name)


def graph_exists(name: str) -> bool:
    """Return True if the named graph has at least one node."""
    db = get_db()
    try:
        g = db.select_graph(name)
        result = g.query("MATCH (n) RETURN count(n) AS c LIMIT 1")
        rows = result.result_set
        return bool(rows and rows[0][0] > 0)
    except Exception:
        return False


def delete_graph(name: str) -> None:
    """Delete a graph if it exists. Silently ignores missing graphs."""
    db = get_db()
    try:
        db.select_graph(name).delete()
    except Exception:
        pass


def ping() -> bool:
    """Return True if FalkorDB responds to a basic query."""
    try:
        g = get_graph("_health_check")
        g.query("RETURN 1")
        return True
    except Exception:
        return False
