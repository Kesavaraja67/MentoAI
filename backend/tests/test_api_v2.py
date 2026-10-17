"""
test_api_v2.py — Integration and endpoint test suite for MentoAI v2 REST API.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.conftest import requires_falkordb

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data


def test_personas_endpoints():
    res = client.get("/api/personas")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 3
    names = [p["id"] for p in data]
    assert "mira" in names
    assert "arjun" in names
    assert "lakshmi" in names


def test_admin_graph_mode_toggle():
    res = client.get("/api/admin/graph-mode")
    assert res.status_code == 200
    assert res.json()["graph_mode_enabled"] is True

    # Toggle off
    res_off = client.post("/api/admin/graph-mode", json={"enabled": False})
    assert res_off.status_code == 200
    assert res_off.json()["graph_mode_enabled"] is False

    # Toggle back on
    res_on = client.post("/api/admin/graph-mode", json={"enabled": True})
    assert res_on.status_code == 200
    assert res_on.json()["graph_mode_enabled"] is True


@requires_falkordb
def test_learner_lifecycle():
    # 1. Create learner
    create_res = client.post("/api/learners", json={
        "display_name": "Test Learner",
        "language": "en",
        "register_text": "inquisitive explorer",
    })
    assert create_res.status_code == 201
    lid = create_res.json()["learner_id"]

    # 2. Start conversation
    conv_res = client.post(f"/api/learners/{lid}/conversations", json={"title": "Session 1"})
    assert conv_res.status_code == 201
    cid = conv_res.json()["conversation_id"]

    # 3. List conversations
    list_res = client.get(f"/api/learners/{lid}/conversations")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 4. Mind view
    mind_res = client.get(f"/api/learners/{lid}/mind")
    assert mind_res.status_code == 200

    # 5. Digest
    dig_res = client.get(f"/api/learners/{lid}/digest")
    assert dig_res.status_code == 200

    # 6. Forget learner (G15)
    forget_res = client.post(f"/api/learners/{lid}/forget")
    assert forget_res.status_code == 200
    assert forget_res.json()["status"] == "forgotten"
