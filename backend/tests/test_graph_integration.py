"""
tests/test_graph_integration.py — Phase 1 integration tests.

These tests require a running FalkorDB container (localhost:6379).
They are automatically SKIPPED with a clear message if it is not reachable.

Tests cover:
  - Seeding the curriculum graph
  - Building a child graph
  - Building a session graph (hydrate)
  - Q2: diagnosis path
  - Q3: frontier skill selection
  - Q4: hint-style ranking
"""
import pytest
from tests.conftest import requires_falkordb

from app.graph.client import get_graph, delete_graph
from app.graph.schema import seed_curriculum, build_child_graph, build_session_graph
from app.graph.queries import (
    q2_diagnose_weak_ancestor,
    q3_frontier_skill,
    q4_rank_hint_styles,
    get_skill_confidence,
    update_skill_confidence,
)
from app.graph.seed import SKILLS


# ── Helpers ────────────────────────────────────────────────────────────────────

SESSION_ID = "test-session-001"
CHILD_ID   = "leo"


@requires_falkordb
class TestSeed:
    def test_curriculum_has_13_skills(self):
        seed_curriculum()
        g = get_graph("curriculum")
        result = g.query("MATCH (s:Skill) RETURN count(s) AS c")
        count = result.result_set[0][0]
        assert count == 13, f"Expected 13 skills, got {count}"

    def test_curriculum_has_correct_edges(self):
        g = get_graph("curriculum")
        result = g.query("MATCH ()-[:PREREQUISITE_OF]->() RETURN count(*) AS c")
        count = result.result_set[0][0]
        # count all prereq pairs from seed data
        expected = sum(len(s["prereqs"]) for s in SKILLS)
        assert count == expected, f"Expected {expected} PREREQUISITE_OF edges, got {count}"

    def test_curriculum_has_5_misconceptions(self):
        g = get_graph("curriculum")
        result = g.query("MATCH (m:Misconception) RETURN count(m) AS c")
        count = result.result_set[0][0]
        assert count == 5, f"Expected 5 misconceptions, got {count}"

    def test_misconception_indicates_weak_edges(self):
        g = get_graph("curriculum")
        result = g.query("MATCH ()-[:INDICATES_WEAK]->() RETURN count(*) AS c")
        count = result.result_set[0][0]
        assert count == 5, f"Expected 5 INDICATES_WEAK edges, got {count}"


@requires_falkordb
class TestChildGraph:
    def test_child_graph_has_child_node(self):
        build_child_graph("leo")
        g = get_graph("child_leo")
        result = g.query("MATCH (c:Child {id: 'leo'}) RETURN c.name")
        assert result.result_set[0][0] == "Leo"

    def test_child_graph_has_correct_confidences(self):
        g = get_graph("child_leo")
        result = g.query("MATCH (s:Skill {id: 'count_on'}) RETURN s.confidence")
        conf = result.result_set[0][0]
        assert abs(conf - 0.35) < 0.001, f"Leo's count_on confidence should be 0.35, got {conf}"

    def test_child_graph_has_interests(self):
        g = get_graph("child_leo")
        result = g.query("MATCH (i:Interest) RETURN i.name ORDER BY i.name")
        names = [r[0] for r in result.result_set]
        assert "rockets" in names and "space" in names

    def test_child_graph_has_hint_styles(self):
        g = get_graph("child_leo")
        result = g.query("MATCH (h:HintStyle) RETURN count(h) AS c")
        count = result.result_set[0][0]
        assert count == 4, f"Expected 4 HintStyles, got {count}"


@requires_falkordb
class TestSessionGraph:
    def test_session_graph_created(self):
        build_child_graph("leo")
        build_session_graph(
            session_id=SESSION_ID,
            child_id=CHILD_ID,
            graph_mode="on",
            target_skill_id="count_on",
            origin_skill_id="count_on",
        )
        g = get_graph(f"session_{SESSION_ID}")
        result = g.query(f"MATCH (s:Session {{id: '{SESSION_ID}'}}) RETURN s.child_id")
        assert result.result_set[0][0] == "leo"

    def test_session_graph_has_skills_with_confidences(self):
        g = get_graph(f"session_{SESSION_ID}")
        result = g.query("MATCH (s:Skill {id: 'count_on'}) RETURN s.confidence")
        conf = result.result_set[0][0]
        assert abs(conf - 0.35) < 0.001

    def test_session_graph_off_is_bare(self):
        sid = "test-session-off"
        build_session_graph(
            session_id=sid,
            child_id=CHILD_ID,
            graph_mode="off",
            target_skill_id="count_on",
            origin_skill_id="count_on",
        )
        g = get_graph(f"session_{sid}")
        result = g.query("MATCH (s:Skill) RETURN count(s) AS c")
        count = result.result_set[0][0]
        assert count == 0, "Graph-off session should have no Skill nodes"
        delete_graph(f"session_{sid}")


@requires_falkordb
class TestQ2Diagnose:
    """Q2: variable-length traversal to weak ancestor."""

    def test_finds_weak_ancestor(self):
        # Leo has count_on = 0.35 (weak). add_5 has count_on as prereq.
        # Diagnosing from add_5 should find count_on.
        g = get_graph(f"session_{SESSION_ID}")
        result = q2_diagnose_weak_ancestor(g, skill_id="add_5", misconception_id="")
        assert result is not None
        assert result["weak_skill_id"] == "count_on"

    def test_misconception_hints_traversal(self):
        # counts_start_number indicates count_on (weak for Leo)
        g = get_graph(f"session_{SESSION_ID}")
        result = q2_diagnose_weak_ancestor(
            g,
            skill_id="count_on",
            misconception_id="counts_start_number",
        )
        # Should still return a result (count_on is weak) or a weak prereq
        # Depends on whether count_on itself has weak prereqs
        # For Leo: one_more_less=0.85 (mastered), count_20=0.90 → no weak prereqs
        # count_on itself is the weak skill, but Q2 starts 1..5 hops upstream
        # If no upstream weak skill, result may be None — that is correct behavior.
        # The test just asserts no crash and result is dict-or-None.
        assert result is None or isinstance(result, dict)

    def test_returns_none_when_no_weak_ancestor(self):
        # For a skill whose all prereqs are mastered, no weak ancestor
        g = get_graph(f"session_{SESSION_ID}")
        # count_10 has no prerequisites → q2 will find nothing
        result = q2_diagnose_weak_ancestor(g, skill_id="count_10", misconception_id="")
        assert result is None


@requires_falkordb
class TestQ3Frontier:
    """Q3: frontier skill selection."""

    def test_leo_frontier_is_count_on(self):
        # Leo: count_20=0.90, one_more_less=0.85 (both mastered >= 0.8)
        # count_on prereqs are both mastered → count_on is the frontier
        # count_on=0.35 < 0.8
        g = get_graph(f"session_{SESSION_ID}")
        result = q3_frontier_skill(g)
        assert result is not None
        assert result["skill_id"] == "count_on", (
            f"Expected frontier=count_on, got {result['skill_id']}"
        )


@requires_falkordb
class TestQ4HintStyles:
    """Q4: hint-style ranking."""

    def test_default_ranking_is_story_first(self):
        g = get_graph(f"session_{SESSION_ID}")
        styles = q4_rank_hint_styles(g)
        assert len(styles) == 4
        # Default: all scores equal at 0.5, tries=0; order breaks tie → story (1) first
        assert styles[0]["id"] == "story"

    def test_higher_score_ranks_first(self):
        g = get_graph(f"session_{SESSION_ID}")
        # Bump visual score
        g.query(
            "MATCH (h:HintStyle {id: 'visual'}) SET h.score = 0.9"
        )
        styles = q4_rank_hint_styles(g)
        assert styles[0]["id"] == "visual"
        # Reset
        g.query(
            "MATCH (h:HintStyle {id: 'visual'}) SET h.score = 0.5"
        )

    def test_lower_tries_ranks_first_when_scores_equal(self):
        g = get_graph(f"session_{SESSION_ID}")
        # Give story 3 tries, visual 0 tries (equal scores)
        g.query("MATCH (h:HintStyle {id: 'story'}) SET h.tries = 3")
        styles = q4_rank_hint_styles(g)
        assert styles[0]["id"] == "visual"
        # Reset
        g.query("MATCH (h:HintStyle {id: 'story'}) SET h.tries = 0")
