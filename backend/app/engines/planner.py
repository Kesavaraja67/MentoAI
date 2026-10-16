"""
engines/planner.py — Deterministic pedagogical planner driven by Cypher graph queries.

Per Section 7.4 of the specification:
Decides the next action after each child attempt:
- advance: when working confidence reaches 0.8+ (mastered), moves to Q3 frontier skill
- return: after 2 consecutive correct on a regressed skill, returns to origin_skill
- praise / same_skill: correct answer, continues practice
- hint: wrong answer (attempts 1 to 3), hint ladder 1-3 with Q4 procedural style selection
- regress: 4th wrong attempt on same problem, regresses to Q2 weak ancestor (or easier numbers)

When graph_mode == "off":
- No graph queries, no decisions written, generic fallback.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any

from app.graph.client import get_graph
from app.graph.queries import (
    q2_diagnose_weak_ancestor,
    q3_frontier_skill,
    q4_rank_hint_styles,
)
from app.graph.trace import (
    write_diagnose_decision,
    write_hint_decision,
    write_regress_decision,
    write_advance_decision,
    write_return_decision,
)


@dataclass
class PlannerOutcome:
    kind: str  # "praise", "hint", "regress", "advance", "return"
    next_skill_id: str
    hint_level: int = 0
    hint_style: str = "story"
    weak_skill_id: Optional[str] = None
    traversal_path: list[str] = field(default_factory=list)
    easier: bool = False
    decision_ids: list[str] = field(default_factory=list)
    origin_skill: Optional[str] = None
    new_consecutive_correct: int = 0
    is_regressed: bool = False


def plan_next_step(
    session_id: str,
    current_skill_id: str,
    correct: bool,
    working_confidence: float,
    attempts_on_current_problem: int,
    consecutive_correct_on_skill: int,
    misconception_id: Optional[str] = None,
    turn_n: int = 1,
    origin_skill: Optional[str] = None,
    graph_mode: str = "on",
) -> PlannerOutcome:
    """
    Evaluates the current state and returns the next pedagogical action.
    """
    g = get_graph(f"session_{session_id}") if graph_mode == "on" else None
    decision_ids: list[str] = []

    # Per spec 7.3: update working confidence in the session graph after each attempt
    if g is not None:
        g.query(
            "MATCH (s:Skill {id: $skill_id}) SET s.confidence = $conf",
            {"skill_id": current_skill_id, "conf": working_confidence},
        )

    # ── BRANCH 1: Child answered CORRECTLY ─────────────────────────────────────
    if correct:
        new_consecutive = consecutive_correct_on_skill + 1

        # Check if skill reached mastery (0.8+)
        if working_confidence >= 0.8:
            if graph_mode == "on" and g is not None:
                frontier = q3_frontier_skill(g)
                if frontier and frontier["skill_id"] != current_skill_id:
                    adv_did = write_advance_decision(
                        session_id=session_id,
                        from_skill_id=current_skill_id,
                        to_skill_id=frontier["skill_id"],
                        achieved_confidence=working_confidence,
                    )
                    decision_ids.append(adv_did)
                    return PlannerOutcome(
                        kind="advance",
                        next_skill_id=frontier["skill_id"],
                        decision_ids=decision_ids,
                        new_consecutive_correct=0,
                        is_regressed=False,
                        origin_skill=None,
                    )

            # Fallback if no frontier or graph off
            return PlannerOutcome(
                kind="praise",
                next_skill_id=current_skill_id,
                decision_ids=decision_ids,
                new_consecutive_correct=new_consecutive,
                is_regressed=bool(origin_skill),
                origin_skill=origin_skill,
            )

        # Check if returning from a regressed skill (2 consecutive correct)
        if origin_skill and origin_skill != current_skill_id and new_consecutive >= 2:
            if graph_mode == "on" and g is not None:
                ret_did = write_return_decision(
                    session_id=session_id,
                    origin_skill_id=origin_skill,
                    regress_skill_id=current_skill_id,
                )
                decision_ids.append(ret_did)

            return PlannerOutcome(
                kind="return",
                next_skill_id=origin_skill,
                decision_ids=decision_ids,
                new_consecutive_correct=0,
                is_regressed=False,
                origin_skill=None,
            )

        # Normal correct: continue on same skill
        return PlannerOutcome(
            kind="praise",
            next_skill_id=current_skill_id,
            decision_ids=decision_ids,
            new_consecutive_correct=new_consecutive,
            is_regressed=bool(origin_skill),
            origin_skill=origin_skill,
        )

    # ── BRANCH 2: Child answered WRONGLY ───────────────────────────────────────
    wrong_attempts = attempts_on_current_problem + 1
    weak_skill_id: Optional[str] = None
    traversal_path: list[str] = []

    # Run Q2 Diagnosis if graph is on
    if graph_mode == "on" and g is not None:
        diag = q2_diagnose_weak_ancestor(
            g,
            skill_id=current_skill_id,
            misconception_id=misconception_id or "",
        )
        if diag:
            weak_skill_id = diag["weak_skill_id"]
            traversal_path = diag.get("path_ids", [])

        diag_did = write_diagnose_decision(
            session_id=session_id,
            misconception_id=misconception_id or "unclassified",
            weak_skill_id=weak_skill_id,
            path_ids=traversal_path,
            turn_n=turn_n,
        )
        decision_ids.append(diag_did)

    # 4th wrong attempt -> REGRESS
    if wrong_attempts >= 4:
        if weak_skill_id and weak_skill_id != current_skill_id:
            if graph_mode == "on" and g is not None:
                reg_did = write_regress_decision(
                    session_id=session_id,
                    origin_skill_id=origin_skill or current_skill_id,
                    regress_to_skill_id=weak_skill_id,
                    turn_n=turn_n,
                )
                decision_ids.append(reg_did)

            return PlannerOutcome(
                kind="regress",
                next_skill_id=weak_skill_id,
                weak_skill_id=weak_skill_id,
                traversal_path=traversal_path,
                decision_ids=decision_ids,
                origin_skill=origin_skill or current_skill_id,
                is_regressed=True,
                new_consecutive_correct=0,
            )
        else:
            # No weak ancestor found in prerequisite DAG -> serve easier numbers on same skill
            return PlannerOutcome(
                kind="regress",
                next_skill_id=current_skill_id,
                weak_skill_id=None,
                traversal_path=traversal_path,
                easier=True,
                decision_ids=decision_ids,
                origin_skill=origin_skill,
                is_regressed=bool(origin_skill),
                new_consecutive_correct=0,
            )

    # Attempts 1, 2, or 3 -> HINT LADDER
    hint_level = wrong_attempts
    chosen_style = "story"

    if graph_mode == "on" and g is not None:
        ranked_styles = q4_rank_hint_styles(g)
        # Spec 7.4: level 1 uses rank 1, level 2 uses rank 2, level 3 uses rank 1 again
        if ranked_styles:
            if hint_level == 1:
                chosen_style = ranked_styles[0]["id"]
            elif hint_level == 2:
                chosen_style = ranked_styles[1]["id"] if len(ranked_styles) > 1 else ranked_styles[0]["id"]
            elif hint_level == 3:
                chosen_style = ranked_styles[0]["id"]

        hint_did = write_hint_decision(
            session_id=session_id,
            hint_level=hint_level,
            hint_style_id=chosen_style,
            skill_id=current_skill_id,
            turn_n=turn_n,
        )
        decision_ids.append(hint_did)

    return PlannerOutcome(
        kind="hint",
        next_skill_id=current_skill_id,
        hint_level=hint_level,
        hint_style=chosen_style,
        weak_skill_id=weak_skill_id,
        traversal_path=traversal_path,
        decision_ids=decision_ids,
        origin_skill=origin_skill,
        is_regressed=bool(origin_skill),
        new_consecutive_correct=0,
    )
