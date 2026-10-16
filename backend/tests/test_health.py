"""
test_health.py — Phase 0 acceptance test.

Tests the /api/health endpoint with a live backend (launched via TestClient).
FalkorDB integration is separately asserted when reachable.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_200():
    """Health endpoint always returns HTTP 200."""
    resp = client.get("/api/health")
    assert resp.status_code == 200


def test_health_has_status_key():
    """Response body must contain a 'status' key."""
    resp = client.get("/api/health")
    body = resp.json()
    assert "status" in body


def test_health_falkordb_key():
    """Response body must contain a 'falkordb' key."""
    resp = client.get("/api/health")
    body = resp.json()
    assert "falkordb" in body
