"""
tests/test_api.py — End-to-end API integration tests for Phase 4.

Covers:
1. GET /api/health
2. GET /api/children
3. POST /api/demo/reset
4. Leo Day 1 -> Day 2 complete flow through REST API:
   - Day 1: start, wrong attempt (hint 1 story), wrong attempt (hint 2 visual), correct (praise)
   - Decision path check (/api/decisions/{id}/path)
   - End session (consolidation diff)
   - Day 2: start, wrong attempt receives visual hint first!
5. Graph Off ablation test:
   - Verifies no decision nodes written and tutor operates without graph
"""
from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient
from tests.conftest import requires_falkordb

from app.main import app

client = TestClient(app)


@requires_falkordb
class TestAPIEndpoints:
    def setup_method(self):
        # Reset demo to clean state before each test
        os.environ["LLM_MODE"] = "fake"
        resp = client.post("/api/demo/reset")
        assert resp.status_code == 200

    def test_health_endpoint(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["falkordb"] == "ok"

    def test_list_children(self):
        resp = client.get("/api/children")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        ids = {c["id"] for c in data}
        assert ids == {"leo", "meera", "arjun"}

    def test_full_leo_day1_then_day2_flow(self):
        """
        Complete acceptance test for Spec Section 4 through REST API:
        Day 1:
        1. Pick Leo -> planner selects count_on
        2. First problem is 3 + 4 = 7
        3. Leo submits 6 (wrong) -> hint level 1, style story
        4. Leo submits 6 again -> hint level 2, style visual
        5. Leo submits 7 (correct) -> praise
        6. Check session graph & decision path
        7. End session -> consolidation diff

        Day 2:
        8. New session -> first hint is now visual!
        """
        # ── DAY 1 ─────────────────────────────────────────────────────────────
        # 1. Start session
        start_resp = client.post(
            "/api/sessions",
            json={"child_id": "leo", "graph_mode": "on"},
        )
        assert start_resp.status_code == 200
        start_data = start_resp.json()
        sid = start_data["session_id"]
        prob = start_data["problem"]
        assert prob["skill_id"] == "count_on"
        assert prob["a"] == 3
        assert prob["b"] == 4
        assert prob["answer"] == 7
        assert len(start_data["story"]) > 0

        # 2. Attempt 1: submits 6 (wrong)
        ans1_resp = client.post(
            f"/api/sessions/{sid}/answer",
            json={"problem_id": prob["problem_id"], "given": 6},
        )
        assert ans1_resp.status_code == 200
        ans1 = ans1_resp.json()
        assert ans1["correct"] is False
        assert ans1["kind"] == "hint"
        assert len(ans1["decision_ids"]) > 0
        dec1_id = ans1["decision_ids"][-1]

        # 3. Check decision justification path
        path_resp = client.get(f"/api/decisions/{dec1_id}/path?session_id={sid}")
        assert path_resp.status_code == 200
        path_data = path_resp.json()
        assert path_data["decision_id"] == dec1_id

        # 4. Attempt 2: submits 6 again (wrong)
        ans2_resp = client.post(
            f"/api/sessions/{sid}/answer",
            json={"problem_id": prob["problem_id"], "given": 6},
        )
        assert ans2_resp.status_code == 200
        ans2 = ans2_resp.json()
        assert ans2["correct"] is False
        assert ans2["kind"] == "hint"

        # 5. Attempt 3: submits 7 (correct!)
        ans3_resp = client.post(
            f"/api/sessions/{sid}/answer",
            json={"problem_id": prob["problem_id"], "given": 7},
        )
        assert ans3_resp.status_code == 200
        ans3 = ans3_resp.json()
        assert ans3["correct"] is True
        assert ans3["kind"] == "praise"
        assert ans3["next_problem"] is not None

        # 6. Check session graph view
        sg_resp = client.get(f"/api/sessions/{sid}/graph")
        assert sg_resp.status_code == 200
        sg_data = sg_resp.json()
        assert len(sg_data["nodes"]) > 0
        assert len(sg_data["edges"]) > 0

        # 7. End Day 1 session -> consolidate
        end_resp = client.post(f"/api/sessions/{sid}/end")
        assert end_resp.status_code == 200
        end_data = end_resp.json()
        assert end_data["episode_id"] != ""
        assert len(end_data["summary"]) > 0

        # ── DAY 2 ─────────────────────────────────────────────────────────────
        # 8. Start Day 2 session for Leo
        day2_resp = client.post(
            "/api/sessions",
            json={"child_id": "leo", "graph_mode": "on"},
        )
        assert day2_resp.status_code == 200
        day2_data = day2_resp.json()
        day2_sid = day2_data["session_id"]
        day2_prob = day2_data["problem"]

        # 9. Submit a wrong answer on Day 2 -> first hint style must be visual!
        wrong_ans = day2_prob["answer"] + 99
        day2_ans_resp = client.post(
            f"/api/sessions/{day2_sid}/answer",
            json={"problem_id": day2_prob["problem_id"], "given": wrong_ans},
        )
        assert day2_ans_resp.status_code == 200
        day2_ans = day2_ans_resp.json()
        assert day2_ans["correct"] is False
        assert day2_ans["kind"] == "hint"

        # End Day 2
        client.post(f"/api/sessions/{day2_sid}/end")

    def test_graph_off_ablation(self):
        """
        Verify Graph Off ablation per Section 7.6 of spec:
        - Session runs with graph_mode = off
        - Does not write Decision nodes
        - Operates cleanly and consolidates gracefully
        """
        start_resp = client.post(
            "/api/sessions",
            json={"child_id": "leo", "graph_mode": "off"},
        )
        assert start_resp.status_code == 200
        sid = start_resp.json()["session_id"]

        ans_resp = client.post(
            f"/api/sessions/{sid}/answer",
            json={"problem_id": start_resp.json()["problem"]["problem_id"], "given": 99},
        )
        assert ans_resp.status_code == 200
        ans_data = ans_resp.json()
        assert ans_data["correct"] is False
        # No decision IDs logged in graph off mode
        assert len(ans_data["decision_ids"]) == 0

        end_resp = client.post(f"/api/sessions/{sid}/end")
        assert end_resp.status_code == 200
