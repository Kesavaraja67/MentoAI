"""
test_mcp.py — Unit tests for MentoAI's FastMCP graph reasoning tools.
"""
import pytest
from app.mcp_server import (
    inspect_learner_snapshot,
    recall_memory,
    find_bridge,
    diagnose_prerequisites,
    explain_decision,
    fetch_mind,
)


class TestMCPServer:
    def test_inspect_learner_snapshot_handles_unknown(self):
        res = inspect_learner_snapshot("unknown_learner_999")
        assert res["found"] is False

    def test_recall_memory_structure(self):
        res = recall_memory("Why do octopuses have 3 hearts?", "mira", top_k=2)
        assert res["query"] == "Why do octopuses have 3 hearts?"
        assert res["learner_id"] == "mira"
        assert isinstance(res["results"], list)

    def test_find_bridge_structure(self):
        res = find_bridge("mira", "buoyancy")
        assert res["learner_id"] == "mira"
        assert res["target_concept"] == "buoyancy"
        assert isinstance(res["bridges"], list)

    def test_diagnose_prerequisites_structure(self):
        res = diagnose_prerequisites("mira", "buoyancy")
        assert res["learner_id"] == "mira"
        assert res["target_concept"] == "buoyancy"
        assert isinstance(res["weak_prerequisites"], list)

    def test_fetch_mind_structure(self):
        res = fetch_mind("mira", limit=10)
        assert "nodes" in res
        assert "edges" in res
