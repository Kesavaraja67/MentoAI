"""
graph/trace.py — Decision node writing helpers.

A Decision captures WHY the system made a choice. It lives in the session
graph during a session, and is copied to the child graph at consolidation.

This module wraps q6_write_decision() with domain-specific helpers for the
four decision kinds used by the Planner.
"""
from __future__ import annotations

from app.graph.client import get_graph
from app.graph.queries import q6_write_decision


def write_select_skill_decision(
    session_id: str,
    chosen_skill_id: str,
    mastered_prereq_ids: list[str],
    frontier_confidence: float,
    episode_id: str | None = None,
) -> str:
    """
    Record a 'select_skill' Decision: the Planner chose a skill to work on.
    BECAUSE edges point to the mastered prerequisites that unlocked this skill,
    and optionally to the Episode from the previous session.
    """
    g = get_graph(f"session_{session_id}")

    summary = (
        f"Chose {chosen_skill_id} (confidence {frontier_confidence:.2f}); "
        f"prerequisites mastered: {', '.join(mastered_prereq_ids) or 'none'}"
    )
    memory_used = ["semantic"]
    if episode_id:
        summary += f"; citing episode {episode_id}"
        memory_used.append("episodic")

    because = [
        {"id": pid, "label": "Skill", "role": "mastered_prereq"}
        for pid in mastered_prereq_ids
    ]
    if episode_id:
        because.append({"id": episode_id, "label": "Episode", "role": "prior_session"})

    return q6_write_decision(
        g,
        session_id=session_id,
        kind="select_skill",
        summary=summary,
        memory_used=memory_used,
        chose_id=chosen_skill_id,
        chose_type="Skill",
        because=because,
    )


def write_diagnose_decision(
    session_id: str,
    misconception_id: str,
    weak_skill_id: str | None,
    path_ids: list[str],
    turn_n: int,
) -> str:
    """
    Record a 'diagnose' Decision: the Assessor identified a misconception and
    the traversal found the underlying weak skill.
    """
    g = get_graph(f"session_{session_id}")

    if weak_skill_id:
        summary = (
            f"Misconception: {misconception_id}. "
            f"Weak ancestor: {weak_skill_id}. "
            f"Path: {' → '.join(path_ids)}"
        )
    else:
        summary = (
            f"Misconception: {misconception_id}. "
            "No weak ancestor found in prerequisite graph."
        )

    because: list[dict] = [
        {"id": str(turn_n), "label": "Turn", "role": "wrong_answer"}
    ]
    if misconception_id != "unclassified":
        because.append({"id": misconception_id, "label": "Misconception", "role": "matched_rule"})
    if weak_skill_id:
        because.append({"id": weak_skill_id, "label": "Skill", "role": "weak_ancestor"})
    for pid in path_ids:
        if pid != weak_skill_id:
            because.append({"id": pid, "label": "Skill", "role": "traversal_path"})

    return q6_write_decision(
        g,
        session_id=session_id,
        kind="diagnose",
        summary=summary,
        memory_used=["working", "semantic"],
        chose_id=weak_skill_id,
        chose_type="Skill" if weak_skill_id else None,
        because=because,
    )


def write_hint_decision(
    session_id: str,
    hint_level: int,
    hint_style_id: str,
    skill_id: str,
    turn_n: int,
) -> str:
    """Record a 'hint' Decision: the Tutor chose a hint level and style."""
    g = get_graph(f"session_{session_id}")

    summary = f"Hint level {hint_level}, style {hint_style_id} for skill {skill_id}"

    return q6_write_decision(
        g,
        session_id=session_id,
        kind="hint",
        summary=summary,
        memory_used=["procedural", "working"],
        chose_id=hint_style_id,
        chose_type="HintStyle",
        because=[{"id": str(turn_n), "label": "Turn", "role": "triggered_by"}],
    )


def write_regress_decision(
    session_id: str,
    origin_skill_id: str,
    regress_to_skill_id: str,
    turn_n: int,
) -> str:
    """Record a 'regress' Decision."""
    g = get_graph(f"session_{session_id}")
    summary = f"Regressed from {origin_skill_id} to {regress_to_skill_id} after 4th wrong attempt"

    return q6_write_decision(
        g,
        session_id=session_id,
        kind="regress",
        summary=summary,
        memory_used=["working"],
        chose_id=regress_to_skill_id,
        chose_type="Skill",
        because=[{"id": str(turn_n), "label": "Turn", "role": "4th_wrong"}],
    )


def write_advance_decision(
    session_id: str,
    from_skill_id: str,
    to_skill_id: str,
    achieved_confidence: float,
) -> str:
    """Record an 'advance' Decision."""
    g = get_graph(f"session_{session_id}")
    summary = (
        f"Advanced from {from_skill_id} to {to_skill_id} "
        f"(confidence reached {achieved_confidence:.2f})"
    )

    return q6_write_decision(
        g,
        session_id=session_id,
        kind="advance",
        summary=summary,
        memory_used=["semantic"],
        chose_id=to_skill_id,
        chose_type="Skill",
        because=[{"id": from_skill_id, "label": "Skill", "role": "mastered"}],
    )


def write_return_decision(
    session_id: str,
    origin_skill_id: str,
    regress_skill_id: str,
) -> str:
    """Record a 'return' Decision after a regress skill is resolved."""
    g = get_graph(f"session_{session_id}")
    summary = (
        f"Returned to {origin_skill_id} after resolving {regress_skill_id}"
    )

    return q6_write_decision(
        g,
        session_id=session_id,
        kind="return",
        summary=summary,
        memory_used=["working"],
        chose_id=origin_skill_id,
        chose_type="Skill",
        because=[{"id": regress_skill_id, "label": "Skill", "role": "resolved"}],
    )
