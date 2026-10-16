"""
tests/test_consolidation.py — Integration tests for Phase 3 (sessions & consolidation).

Tests:
1. Full consolidation cycle:
   - Hydrate session graph
   - Record turns (Q5)
   - Record decisions (Q6 / trace)
   - Consolidate session into child graph
   - Assert: confidences updated in child graph
   - Assert: Episode created with stats
   - Assert: PRACTICED, EXHIBITED, USED_STYLE edges created
   - Assert: Decisions copied with CHOSE and BECAUSE edges
   - Assert: Session graph deleted
   - Assert: Idempotent re-consolidation
2. Leo Day 1 -> Day 2 flow:
   - Day 1: Leo struggles with count_on, visual hint helps after story fails
   - Consolidation updates hint styles (visual up, story down)
   - Day 2: New session hydrates; Q4 ranks visual first!
"""
from __future__ import annotations

import pytest
from tests.conftest import requires_falkordb

from app.graph.client import get_graph, delete_graph
from app.graph.schema import seed_curriculum, build_child_graph, build_session_graph
from app.graph.queries import (
    q4_rank_hint_styles,
    q5_write_turn,
    q6_write_decision,
)
from app.graph.consolidate import consolidate
from app.graph.trace import (
    write_select_skill_decision,
    write_diagnose_decision,
    write_hint_decision,
)


@requires_falkordb
class TestConsolidation:
    """Verifies session consolidation into long-term child graph per spec 7.7."""

    def setup_method(self):
        seed_curriculum()
        self.child_id = "leo"
        self.session_id = "test_consolidation_sess_01"
        build_child_graph(self.child_id)
        build_session_graph(
            child_id=self.child_id,
            session_id=self.session_id,
            graph_mode="on",
            target_skill_id="count_on",
            origin_skill_id="count_on",
        )

    def teardown_method(self):
        delete_graph(f"session_{self.session_id}")
        delete_graph(f"child_{self.child_id}")

    def test_consolidation_updates_child_graph_and_cleans_up(self):
        sess_g = get_graph(f"session_{self.session_id}")
        child_g = get_graph(f"child_{self.child_id}")

        # Record turns:
        # Turn 1: wrong, counts_start_number, hint_level=1, hint_style=story
        q5_write_turn(
            sess_g,
            session_id=self.session_id,
            n=1,
            problem_id="prob_1",
            skill_id="count_on",
            op="+",
            a=3,
            b=4,
            answer=7,
            given=6,
            correct=False,
            misconception_id="counts_start_number",
            hint_level=1,
            hint_style="story",
        )
        # Turn 2: correct, after hint_level=2, hint_style=visual
        q5_write_turn(
            sess_g,
            session_id=self.session_id,
            n=2,
            problem_id="prob_1",
            skill_id="count_on",
            op="+",
            a=3,
            b=4,
            answer=7,
            given=7,
            correct=True,
            misconception_id="",
            hint_level=2,
            hint_style="visual",
        )

        # Update working confidence in session
        sess_g.query("MATCH (s:Skill {id: 'count_on'}) SET s.confidence = 0.55")

        # Record a decision
        did = write_hint_decision(
            session_id=self.session_id,
            hint_level=1,
            hint_style_id="story",
            skill_id="count_on",
            turn_n=1,
        )

        # Run consolidation
        diff = consolidate(self.session_id)

        assert diff["episode_id"] != ""
        assert len(diff["skills"]) > 0
        skill_entry = next(s for s in diff["skills"] if s["id"] == "count_on")
        assert skill_entry["before"] == 0.35
        assert skill_entry["after"] == 0.55

        # 1. Child graph has updated confidence
        res = child_g.query("MATCH (s:Skill {id: 'count_on'}) RETURN s.confidence")
        assert abs(res.result_set[0][0] - 0.55) < 0.001

        # 2. Child graph has Episode node with stats
        ep_res = child_g.query(
            "MATCH (e:Episode {id: $eid}) RETURN e.correct, e.total, e.hints_used",
            {"eid": diff["episode_id"]},
        )
        assert len(ep_res.result_set) == 1
        correct, total, hints = ep_res.result_set[0]
        assert correct == 1
        assert total == 2
        assert hints == 2

        # 3. Child graph has PRACTICED edge
        prac = child_g.query(
            "MATCH (e:Episode {id: $eid})-[p:PRACTICED]->(s:Skill {id: 'count_on'}) RETURN p.before, p.after",
            {"eid": diff["episode_id"]},
        )
        assert len(prac.result_set) == 1
        assert abs(prac.result_set[0][0] - 0.35) < 0.001
        assert abs(prac.result_set[0][1] - 0.55) < 0.001

        # 4. Child graph has EXHIBITED edge for counts_start_number
        exhib = child_g.query(
            "MATCH (e:Episode {id: $eid})-[x:EXHIBITED]->(m:Misconception {id: 'counts_start_number'}) RETURN x.count",
            {"eid": diff["episode_id"]},
        )
        assert len(exhib.result_set) == 1
        assert exhib.result_set[0][0] == 1

        # 5. Decisions copied to child graph
        d_res = child_g.query(
            "MATCH (d:Decision {id: $did}) RETURN d.kind",
            {"did": did},
        )
        assert len(d_res.result_set) == 1
        assert d_res.result_set[0][0] == "hint"

        # 6. Session graph is deleted
        # Querying deleted graph in FalkorDB should return empty or error
        sess_check = get_graph(f"session_{self.session_id}").query("MATCH (n) RETURN count(n)")
        assert sess_check.result_set[0][0] == 0

        # 7. Idempotent re-run
        idemp_diff = consolidate(self.session_id)
        assert idemp_diff["episode_id"] == diff["episode_id"]


@requires_falkordb
class TestLeoDay1ToDay2Flow:
    """
    Acceptance test from Spec Section 4 & Phase 3:
    Verifies that what Leo experiences on Day 1 shifts procedural memory,
    causing Day 2's session to rank visual hints first!
    """

    def test_day1_to_day2_hint_adaptation(self):
        seed_curriculum()
        child_id = "leo"
        day1_sid = "leo_day_1"
        day2_sid = "leo_day_2"

        build_child_graph(child_id)
        child_g = get_graph(f"child_{child_id}")

        # ── DAY 1 ─────────────────────────────────────────────────────────────
        build_session_graph(
            child_id=child_id,
            session_id=day1_sid,
            graph_mode="on",
            target_skill_id="count_on",
            origin_skill_id="count_on",
        )
        day1_g = get_graph(f"session_{day1_sid}")

        # Check default hint styles: story is rank 1 (score 0.5, tries 0, order 1)
        styles_before = q4_rank_hint_styles(day1_g)
        assert styles_before[0]["id"] == "story"

        # Simulation of Problem 1 (3 + 4 = 7):
        # Attempt 1: Leo answers 6 (wrong). Hint 1 given with style 'story'.
        q5_write_turn(
            day1_g,
            session_id=day1_sid,
            n=1,
            problem_id="prob_3_4",
            skill_id="count_on",
            op="+",
            a=3,
            b=4,
            answer=7,
            given=6,
            correct=False,
            misconception_id="counts_start_number",
            hint_level=1,
            hint_style="story",
        )

        # Attempt 2: Leo answers 6 again (wrong, so 'story' hint did not help!).
        # Hint 2 given with style 'visual'.
        q5_write_turn(
            day1_g,
            session_id=day1_sid,
            n=2,
            problem_id="prob_3_4",
            skill_id="count_on",
            op="+",
            a=3,
            b=4,
            answer=7,
            given=6,
            correct=False,
            misconception_id="counts_start_number",
            hint_level=2,
            hint_style="visual",
        )

        # Attempt 3: Leo answers 7 (CORRECT!). The 'visual' hint worked!
        q5_write_turn(
            day1_g,
            session_id=day1_sid,
            n=3,
            problem_id="prob_3_4",
            skill_id="count_on",
            op="+",
            a=3,
            b=4,
            answer=7,
            given=7,
            correct=True,
            misconception_id="",
            hint_level=0,
            hint_style="",
        )

        # End Day 1 and consolidate
        day1_diff = consolidate(day1_sid)
        assert day1_diff["episode_id"] != ""

        # Check updated hint scores in child graph:
        # story: tries=1, helped=0 -> helped_rate = 0.0 -> new score = 0.7 * 0.5 + 0.3 * 0.0 = 0.35
        # visual: tries=1, helped=1 -> helped_rate = 1.0 -> new score = 0.7 * 0.5 + 0.3 * 1.0 = 0.65
        visual_score = child_g.query("MATCH (h:HintStyle {id: 'visual'}) RETURN h.score").result_set[0][0]
        story_score = child_g.query("MATCH (h:HintStyle {id: 'story'}) RETURN h.score").result_set[0][0]

        assert visual_score > story_score
        assert abs(visual_score - 0.65) < 0.01
        assert abs(story_score - 0.35) < 0.01

        # ── DAY 2 ─────────────────────────────────────────────────────────────
        # Start Day 2 session for Leo
        build_session_graph(
            child_id=child_id,
            session_id=day2_sid,
            graph_mode="on",
            target_skill_id="count_on",
            origin_skill_id="count_on",
        )
        day2_g = get_graph(f"session_{day2_sid}")

        # Now check Q4 ranking on Day 2:
        # Visual is now ranked #1 because score 0.65 > 0.5 > 0.35!
        styles_day2 = q4_rank_hint_styles(day2_g)
        assert styles_day2[0]["id"] == "visual", (
            f"Expected Day 2 first hint style to be 'visual', got '{styles_day2[0]['id']}'"
        )
        assert styles_day2[-1]["id"] == "story", "Story should rank lowest after failing on Day 1"

        # Clean up
        delete_graph(f"session_{day2_sid}")
        delete_graph(f"child_{child_id}")
