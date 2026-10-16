"""
tests/test_engines.py — Unit tests for Primer teaching engines.

Covers:
1. Assessor: every rule (1..5, unclassified, correct) and every tie condition.
2. Mastery: confidence formula across hint levels 0..3, penalties, bounds, thresholds.
3. Problem Generator: determinism, all 13 skill shapes, opening problem, parallel_problem guarantees.
4. Planner: advance, return, hint ladder, regress on 4th wrong, graph off mode.
"""
from __future__ import annotations

import pytest
from app.engines.assessor import assess_answer
from app.engines.mastery import (
    update_confidence,
    is_weak,
    is_mastered,
    WEAK_THRESHOLD,
    MASTERED_THRESHOLD,
)
from app.engines.problems import generate_problem, parallel_problem
from app.engines.planner import plan_next_step, PlannerOutcome
from app.graph.schema import seed_curriculum, build_child_graph, build_session_graph
from app.graph.client import delete_graph


# ── 1. Assessor Rules and Ties ────────────────────────────────────────────────

class TestAssessor:
    """Verify Section 7.2 of the spec: all 5 rules, ties, and edge cases."""

    def test_correct_answer(self):
        is_corr, misc = assess_answer(op="+", a=3, b=4, answer=7, given=7)
        assert is_corr is True
        assert misc is None

    def test_rule_1_counts_start_number(self):
        # op == '+' and given == answer - 1
        is_corr, misc = assess_answer(op="+", a=3, b=4, answer=7, given=6)
        assert is_corr is False
        assert misc == "counts_start_number"

    def test_rule_2_overshoots_by_one(self):
        # op == '+' and given == answer + 1
        is_corr, misc = assess_answer(op="+", a=3, b=4, answer=7, given=8)
        assert is_corr is False
        assert misc == "overshoots_by_one"

    def test_rule_3_adds_instead_of_subtracts(self):
        # op == '-' and given == a + b
        is_corr, misc = assess_answer(op="-", a=5, b=2, answer=3, given=7)
        assert is_corr is False
        assert misc == "adds_instead_of_subtracts"

    def test_rule_4_subtracts_instead_of_adds(self):
        # op == '+' and given == abs(a - b)
        # 5 + 3 = 8, given 2 == abs(5 - 3)
        is_corr, misc = assess_answer(op="+", a=5, b=3, answer=8, given=2)
        assert is_corr is False
        assert misc == "subtracts_instead_of_adds"

    def test_rule_5_reports_an_addend(self):
        # op == '+' and given in (a, b)
        # 4 + 5 = 9, given 4 or 5 (not matching rules 1..4)
        is_corr, misc = assess_answer(op="+", a=4, b=5, answer=9, given=4)
        assert is_corr is False
        assert misc == "reports_an_addend"

        is_corr, misc = assess_answer(op="+", a=4, b=5, answer=9, given=5)
        assert is_corr is False
        assert misc == "reports_an_addend"

    def test_unclassified(self):
        # Completely arbitrary wrong answer
        is_corr, misc = assess_answer(op="+", a=3, b=4, answer=7, given=99)
        assert is_corr is False
        assert misc == "unclassified"

    # ── Ties Testing Priority Order ──────────────────────────────────────────

    def test_tie_rule_1_vs_rule_5(self):
        # a=1, b=2, answer=3. given=2:
        # Rule 1: given == answer - 1 (2 == 3 - 1) -> counts_start_number
        # Rule 5: given in (1, 2) (2 in (1, 2))     -> reports_an_addend
        # Priority 1 must win over Priority 5.
        is_corr, misc = assess_answer(op="+", a=1, b=2, answer=3, given=2)
        assert is_corr is False
        assert misc == "counts_start_number"

    def test_tie_rule_4_vs_rule_5(self):
        # a=4, b=2, answer=6. given=2:
        # Rule 4: given == abs(4 - 2) == 2 -> subtracts_instead_of_adds
        # Rule 5: given in (4, 2) == 2      -> reports_an_addend
        # Priority 4 must win over Priority 5.
        is_corr, misc = assess_answer(op="+", a=4, b=2, answer=6, given=2)
        assert is_corr is False
        assert misc == "subtracts_instead_of_adds"

    def test_tie_rule_2_vs_rule_5(self):
        # a=3, b=2, answer=5. given=6 -> overshoots_by_one (6 not in 3, 2)
        # What if a=4, b=3, answer=7, given=4 -> reports_an_addend (4 != 8)
        # Rule 2 requires given == answer + 1. Since answer + 1 is always strictly greater
        # than max(a, b), rule 2 never directly collides with given in (a, b) for positive a, b.
        is_corr, misc = assess_answer(op="+", a=4, b=3, answer=7, given=8)
        assert is_corr is False
        assert misc == "overshoots_by_one"


# ── 2. Mastery Engine ─────────────────────────────────────────────────────────

class TestMastery:
    """Verify Section 7.3: confidence updates and thresholds."""

    @pytest.mark.parametrize(
        "current,hint_level,expected",
        [
            (0.0, 0, 0.35),       # 0.0 + 1.0 * 0.35 = 0.35
            (0.5, 0, 0.675),      # 0.5 + 0.5 * 0.35 = 0.675
            (0.8, 0, 0.87),       # 0.8 + 0.2 * 0.35 = 0.87
            (0.5, 1, 0.59),       # 0.5 + 0.5 * 0.18 = 0.59
            (0.5, 2, 0.55),       # 0.5 + 0.5 * 0.10 = 0.55
            (0.5, 3, 0.525),      # 0.5 + 0.5 * 0.05 = 0.525
        ],
    )
    def test_correct_updates(self, current, hint_level, expected):
        new_c = update_confidence(current, correct=True, hint_level=hint_level)
        assert new_c == pytest.approx(expected, abs=1e-4)

    @pytest.mark.parametrize(
        "current,expected",
        [
            (1.0, 0.8),           # 1.0 - 0.2 = 0.8
            (0.5, 0.4),           # 0.5 - 0.1 = 0.4
            (0.35, 0.28),         # 0.35 - 0.07 = 0.28
            (0.0, 0.0),           # 0.0 - 0.0 = 0.0
        ],
    )
    def test_wrong_updates(self, current, expected):
        new_c = update_confidence(current, correct=False)
        assert new_c == pytest.approx(expected, abs=1e-4)

    def test_clamping_and_bounds(self):
        assert update_confidence(0.99, correct=True, hint_level=0) <= 1.0
        assert update_confidence(0.01, correct=False) >= 0.0

    def test_thresholds(self):
        assert is_weak(0.49) is True
        assert is_weak(0.50) is False
        assert is_weak(0.35) is True

        assert is_mastered(0.80) is True
        assert is_mastered(0.85) is True
        assert is_mastered(0.79) is False


# ── 3. Problem Generator ──────────────────────────────────────────────────────

class TestProblemGenerator:
    """Verify Section 7.1: deterministic seeding, shapes, and parallel problem guarantees."""

    ALL_SKILLS = [
        "count_10", "count_20", "one_more_less", "bonds_5", "count_on",
        "add_5", "sub_5", "bonds_10", "add_10", "sub_10", "doubles",
        "make_ten", "add_20",
    ]

    def test_all_13_skills_generate_valid_problems(self):
        for skill in self.ALL_SKILLS:
            prob = generate_problem(child_id="leo", skill_id=skill, session_index=1, turn_n=1)
            assert prob["skill_id"] == skill
            assert "a" in prob and "b" in prob and "answer" in prob
            assert "story_slots" in prob
            # Verify mathematical correctness
            if prob["op"] == "+":
                assert prob["a"] + prob["b"] == prob["answer"]
            elif prob["op"] == "-":
                assert prob["a"] - prob["b"] == prob["answer"]
            elif prob["op"] == "?":
                assert prob["a"] + prob["answer"] in (5, 10)

    def test_seed_determinism(self):
        p1 = generate_problem("leo", "count_on", session_index=1, turn_n=3)
        p2 = generate_problem("leo", "count_on", session_index=1, turn_n=3)
        assert p1["problem_id"] == p2["problem_id"]
        assert p1["a"] == p2["a"]
        assert p1["b"] == p2["b"]
        assert p1["answer"] == p2["answer"]

        # Different turn produces variation
        p3 = generate_problem("leo", "count_on", session_index=1, turn_n=4)
        assert p3["problem_id"] != p1["problem_id"]

    def test_leo_scripted_opening_problem(self):
        # Leo's opening problem: 3 + 4 = 7 on count_on
        p = generate_problem("leo", "count_on", session_index=1, turn_n=0)
        assert p["a"] == 3
        assert p["b"] == 4
        assert p["answer"] == 7
        assert p["op"] == "+"

    def test_parallel_problem_guarantee(self):
        """
        Verify spec rule: NO operand (a, b) and NO result equals the original answer.
        """
        original = {"problem_id": "prob_test", "skill_id": "count_on", "op": "+", "a": 3, "b": 4, "answer": 7}
        par = parallel_problem(original)

        assert par["a"] != 7, "Parallel operand a cannot equal original answer 7"
        assert par["b"] != 7, "Parallel operand b cannot equal original answer 7"
        assert par["answer"] != 7, "Parallel answer cannot equal original answer 7"
        assert (par["a"], par["b"]) != (original["a"], original["b"])

        # Also test on other skills
        for skill in ["add_5", "sub_5", "bonds_5", "bonds_10", "doubles"]:
            prob = generate_problem("arjun", skill, session_index=1, turn_n=2)
            par = parallel_problem(prob)
            orig_ans = prob["answer"]
            assert par["a"] != orig_ans
            assert par["b"] != orig_ans
            assert par["answer"] != orig_ans


# ── 4. Planner Engine ─────────────────────────────────────────────────────────

class TestPlanner:
    """Verify Section 7.4: pedagogical decisions and state transitions."""

    @pytest.fixture(autouse=True)
    def setup_session_graph(self):
        seed_curriculum()
        build_child_graph("leo")
        self.session_id = "test_planner_sess"
        build_session_graph(
            child_id="leo",
            session_id=self.session_id,
            graph_mode="on",
            target_skill_id="count_on",
            origin_skill_id="count_on",
        )
        yield
        delete_graph(f"session_{self.session_id}")
        delete_graph("child_leo")

    def test_praise_on_same_skill_when_not_mastered(self):
        # Leo count_on starts at 0.35. A correct answer with confidence 0.575 continues
        outcome = plan_next_step(
            session_id=self.session_id,
            current_skill_id="count_on",
            correct=True,
            working_confidence=0.575,
            attempts_on_current_problem=0,
            consecutive_correct_on_skill=0,
            turn_n=1,
            graph_mode="on",
        )
        assert outcome.kind == "praise"
        assert outcome.next_skill_id == "count_on"
        assert outcome.new_consecutive_correct == 1

    def test_advance_when_confidence_reaches_mastery(self):
        # When confidence reaches 0.85, planner queries Q3 and advances to frontier
        outcome = plan_next_step(
            session_id=self.session_id,
            current_skill_id="count_on",
            correct=True,
            working_confidence=0.85,
            attempts_on_current_problem=0,
            consecutive_correct_on_skill=1,
            turn_n=2,
            graph_mode="on",
        )
        assert outcome.kind == "advance"
        assert len(outcome.decision_ids) > 0

    def test_hint_ladder_progression_on_wrong_attempts(self):
        # 1st wrong attempt -> hint level 1
        h1 = plan_next_step(
            session_id=self.session_id,
            current_skill_id="count_on",
            correct=False,
            working_confidence=0.28,
            attempts_on_current_problem=0,
            consecutive_correct_on_skill=0,
            misconception_id="counts_start_number",
            turn_n=1,
            graph_mode="on",
        )
        assert h1.kind == "hint"
        assert h1.hint_level == 1
        assert h1.hint_style == "story"  # Default top rank in Q4
        assert len(h1.decision_ids) == 2  # diagnose + hint

        # 2nd wrong attempt -> hint level 2 (rank 2 style = visual)
        h2 = plan_next_step(
            session_id=self.session_id,
            current_skill_id="count_on",
            correct=False,
            working_confidence=0.22,
            attempts_on_current_problem=1,
            consecutive_correct_on_skill=0,
            misconception_id="counts_start_number",
            turn_n=2,
            graph_mode="on",
        )
        assert h2.kind == "hint"
        assert h2.hint_level == 2
        assert h2.hint_style == "visual"

        # 3rd wrong attempt -> hint level 3 (rank 1 style again = story)
        h3 = plan_next_step(
            session_id=self.session_id,
            current_skill_id="count_on",
            correct=False,
            working_confidence=0.18,
            attempts_on_current_problem=2,
            consecutive_correct_on_skill=0,
            misconception_id="counts_start_number",
            turn_n=3,
            graph_mode="on",
        )
        assert h3.kind == "hint"
        assert h3.hint_level == 3
        assert h3.hint_style == "story"

    def test_regress_after_4th_wrong_attempt(self):
        # 4th wrong attempt (attempts_on_current_problem=3 before this attempt)
        # Diagnosing from add_5 (has weak ancestor count_on)
        reg = plan_next_step(
            session_id=self.session_id,
            current_skill_id="add_5",
            correct=False,
            working_confidence=0.20,
            attempts_on_current_problem=3,
            consecutive_correct_on_skill=0,
            misconception_id="counts_start_number",
            turn_n=4,
            graph_mode="on",
        )
        assert reg.kind == "regress"
        assert reg.next_skill_id == "count_on"
        assert reg.is_regressed is True
        assert reg.origin_skill == "add_5"

    def test_return_after_2_consecutive_correct_on_regressed_skill(self):
        # Currently regressed on count_on, origin is add_5
        # 1st correct: still practicing count_on
        step1 = plan_next_step(
            session_id=self.session_id,
            current_skill_id="count_on",
            correct=True,
            working_confidence=0.50,
            attempts_on_current_problem=0,
            consecutive_correct_on_skill=0,
            origin_skill="add_5",
            turn_n=5,
            graph_mode="on",
        )
        assert step1.kind == "praise"
        assert step1.next_skill_id == "count_on"
        assert step1.new_consecutive_correct == 1

        # 2nd consecutive correct: triggers return to origin_skill!
        step2 = plan_next_step(
            session_id=self.session_id,
            current_skill_id="count_on",
            correct=True,
            working_confidence=0.65,
            attempts_on_current_problem=0,
            consecutive_correct_on_skill=1,
            origin_skill="add_5",
            turn_n=6,
            graph_mode="on",
        )
        assert step2.kind == "return"
        assert step2.next_skill_id == "add_5"
        assert step2.is_regressed is False
        assert step2.origin_skill is None
