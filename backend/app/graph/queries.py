"""
graph/queries.py — Thin query runner.

Loads named .cypher files from graph/queries/ and exposes typed helper
functions for each query. This is the ONLY place in the codebase where
Cypher strings are executed; all query text lives in the .cypher files.

Each function takes a graph handle and named parameters.
It returns raw result rows so callers can interpret them.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import falkordb

_QUERY_DIR = Path(__file__).parent / "queries"


def _load(filename: str) -> str:
    """
    Read a .cypher file from the queries directory.
    FalkorDB does NOT support SQL-style '--' comments, so we strip them here.
    The .cypher files keep their comments for human readability; comments are
    removed before the query is sent to FalkorDB.
    (Fix recorded in docs/QUERIES.md.)
    """
    path = _QUERY_DIR / filename
    raw = path.read_text(encoding="utf-8")
    lines = [line for line in raw.splitlines() if not line.strip().startswith("--")]
    return "\n".join(lines)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Q1: child summary ─────────────────────────────────────────────────────────

def q1_child_summary(g: falkordb.Graph, child_id: str) -> dict | None:
    cypher = _load("q1_child_summary.cypher")
    result = g.query(cypher, {"child_id": child_id})
    if not result.result_set:
        return None
    row = result.result_set[0]
    return {
        "child_id":  row[0],
        "name":      row[1],
        "age":       row[2],
        "interests": row[3] or [],
        "skills":    row[4] or [],
    }


# ── Q2: diagnose weak ancestor ────────────────────────────────────────────────

def q2_diagnose_weak_ancestor(
    g: falkordb.Graph,
    skill_id: str,
    misconception_id: str,
) -> dict | None:
    """
    Returns a dict with keys: weak_skill_id, weak_skill_name,
    weak_confidence, path_ids.
    Returns None if no weak ancestor is found.
    """
    cypher = _load("q2_diagnose_weak_ancestor.cypher")
    result = g.query(cypher, {"skill_id": skill_id, "misconception_id": misconception_id})
    if not result.result_set:
        return None
    row = result.result_set[0]
    return {
        "weak_skill_id":   row[0],
        "weak_skill_name": row[1],
        "weak_confidence": row[2],
        "path_ids":        row[3] if row[3] else [],
    }


# ── Q3: frontier skill ────────────────────────────────────────────────────────

def q3_frontier_skill(g: falkordb.Graph) -> dict | None:
    """
    Returns a dict with keys: skill_id, skill_name, confidence.
    Returns None if no frontier skill exists (all skills mastered or no prereqs met).
    """
    cypher = _load("q3_frontier_skill.cypher")
    result = g.query(cypher)
    if not result.result_set:
        return None
    row = result.result_set[0]
    return {"skill_id": row[0], "skill_name": row[1], "confidence": row[2]}


# ── Q4: rank hint styles ──────────────────────────────────────────────────────

def q4_rank_hint_styles(g: falkordb.Graph) -> list[dict]:
    """
    Returns a list of dicts [{id, order, score, tries}] ordered best first.
    """
    cypher = _load("q4_rank_hint_styles.cypher")
    result = g.query(cypher)
    return [
        {"id": r[0], "order": r[1], "score": r[2], "tries": r[3]}
        for r in result.result_set
    ]


# ── Q5: write turn ────────────────────────────────────────────────────────────

def q5_write_turn(
    g: falkordb.Graph,
    session_id: str,
    n: int,
    problem_id: str,
    skill_id: str,
    op: str,
    a: int,
    b: int,
    answer: int,
    given: int,
    correct: bool,
    misconception_id: str,
    hint_level: int,
    hint_style: str,
) -> int:
    """Create a Turn node and return its turn number."""
    cypher = _load("q5_write_turn.cypher")
    result = g.query(
        cypher,
        {
            "session_id":      session_id,
            "n":               n,
            "problem_id":      problem_id,
            "skill_id":        skill_id,
            "op":              op,
            "a":               a,
            "b":               b,
            "answer":          answer,
            "given":           given,
            "correct":         correct,
            "misconception_id":misconception_id,
            "hint_level":      hint_level,
            "hint_style":      hint_style,
            "ts":              _now(),
        },
    )
    return result.result_set[0][0]


# ── Q6: write decision ────────────────────────────────────────────────────────

def q6_write_decision(
    g: falkordb.Graph,
    session_id: str,
    kind: str,
    summary: str,
    memory_used: list[str],
    chose_id: str | None = None,
    chose_type: str | None = None,   # "Skill" | "HintStyle"
    because: list[dict] | None = None,  # [{id, label, role}]
) -> str:
    """
    Write a Decision node and its CHOSE / BECAUSE edges.
    Returns the decision_id.
    """
    decision_id = str(uuid.uuid4())
    cypher = _load("q6_write_decision.cypher")
    g.query(
        cypher,
        {
            "decision_id":  decision_id,
            "ts":           _now(),
            "kind":         kind,
            "summary":      summary,
            "memory_used":  memory_used,
            "session_id":   session_id,
        },
    )

    # CHOSE edge
    if chose_id and chose_type:
        _write_chose_edge(g, decision_id, chose_id, chose_type)

    # BECAUSE edges (one query per edge — FalkorDB needs known label at parse time)
    for b in (because or []):
        _write_because_edge(g, decision_id, b["id"], b["label"], b["role"])

    return decision_id


def _write_chose_edge(
    g: falkordb.Graph, decision_id: str, target_id: str, target_type: str
) -> None:
    if target_type == "Skill":
        g.query(
            """
            MATCH (d:Decision {id: $did}), (t:Skill {id: $tid})
            CREATE (d)-[:CHOSE]->(t)
            """,
            {"did": decision_id, "tid": target_id},
        )
    elif target_type == "HintStyle":
        g.query(
            """
            MATCH (d:Decision {id: $did}), (t:HintStyle {id: $tid})
            CREATE (d)-[:CHOSE]->(t)
            """,
            {"did": decision_id, "tid": target_id},
        )


def _write_because_edge(
    g: falkordb.Graph,
    decision_id: str,
    target_id: str,
    target_label: str,
    role: str,
) -> None:
    if target_label == "Skill":
        g.query(
            """
            MATCH (d:Decision {id: $did}), (t:Skill {id: $tid})
            CREATE (d)-[:BECAUSE {role: $role}]->(t)
            """,
            {"did": decision_id, "tid": target_id, "role": role},
        )
    elif target_label == "Misconception":
        g.query(
            """
            MATCH (d:Decision {id: $did}), (t:Misconception {id: $tid})
            CREATE (d)-[:BECAUSE {role: $role}]->(t)
            """,
            {"did": decision_id, "tid": target_id, "role": role},
        )
    elif target_label == "Episode":
        g.query(
            """
            MATCH (d:Decision {id: $did}), (t:Episode {id: $tid})
            CREATE (d)-[:BECAUSE {role: $role}]->(t)
            """,
            {"did": decision_id, "tid": target_id, "role": role},
        )
    elif target_label == "Turn":
        g.query(
            """
            MATCH (d:Decision {id: $did}), (t:Turn {n: $tn})
            CREATE (d)-[:BECAUSE {role: $role}]->(t)
            """,
            {"did": decision_id, "tn": int(target_id), "role": role},
        )


# ── Q7: get session turns ─────────────────────────────────────────────────────

def q7_get_session_turns(g: falkordb.Graph, session_id: str) -> list[dict]:
    """
    Returns a list of dicts, one per Turn, in order.
    Also includes session metadata in each row (child_id, started_at, graph_mode).
    """
    cypher = _load("q7_get_session_turns.cypher")
    result = g.query(cypher, {"session_id": session_id})
    rows = []
    for r in result.result_set:
        rows.append({
            "child_id":        r[0],
            "started_at":      r[1],
            "graph_mode":      r[2],
            "turn_n":          r[3],
            "problem_id":      r[4],
            "skill_id":        r[5],
            "op":              r[6],
            "a":               r[7],
            "b":               r[8],
            "answer":          r[9],
            "given":           r[10],
            "correct":         r[11],
            "misconception_id":r[12],
            "hint_level":      r[13],
            "hint_style":      r[14],
            "ts":              r[15],
        })
    return rows


# ── Q8: decision path ─────────────────────────────────────────────────────────

def q8_decision_path(g: falkordb.Graph, decision_id: str) -> list[dict]:
    """
    Returns the subgraph for one Decision: chose + because targets.
    """
    cypher = _load("q8_decision_path.cypher")
    result = g.query(cypher, {"decision_id": decision_id})
    rows = []
    for r in result.result_set:
        rows.append({
            "decision_id":   r[0],
            "kind":          r[1],
            "summary":       r[2],
            "memory_used":   r[3],
            "chose_id":      r[4],
            "chose_label":   r[5],
            "because_id":    r[6],
            "because_label": r[7],
            "because_role":  r[8],
        })
    return rows


# ── Mastery update (in-graph) ─────────────────────────────────────────────────

def update_skill_confidence(
    g: falkordb.Graph, skill_id: str, new_confidence: float
) -> None:
    """Update the confidence of a Skill node in the given graph."""
    g.query(
        "MATCH (s:Skill {id: $sid}) SET s.confidence = $conf",
        {"sid": skill_id, "conf": new_confidence},
    )


def get_skill_confidence(g: falkordb.Graph, skill_id: str) -> float:
    """Read the current confidence for a skill from the graph."""
    result = g.query(
        "MATCH (s:Skill {id: $sid}) RETURN s.confidence",
        {"sid": skill_id},
    )
    if result.result_set:
        return result.result_set[0][0]
    return 0.0


def get_session_meta(g: falkordb.Graph, session_id: str) -> dict:
    """Return the Session node properties."""
    result = g.query(
        """
        MATCH (s:Session {id: $sid})
        RETURN s.id, s.child_id, s.graph_mode, s.turn_count,
               s.target_skill, s.origin_skill, s.started_at
        """,
        {"sid": session_id},
    )
    if not result.result_set:
        raise ValueError(f"Session {session_id} not found")
    r = result.result_set[0]
    return {
        "id":            r[0],
        "child_id":      r[1],
        "graph_mode":    r[2],
        "turn_count":    r[3],
        "target_skill":  r[4],
        "origin_skill":  r[5],
        "started_at":    r[6],
    }


def update_session_target(
    g: falkordb.Graph, session_id: str, target_skill: str, origin_skill: str
) -> None:
    g.query(
        """
        MATCH (s:Session {id: $sid})
        SET s.target_skill = $target, s.origin_skill = $origin
        """,
        {"sid": session_id, "target": target_skill, "origin": origin_skill},
    )


def get_interests(g: falkordb.Graph) -> list[str]:
    """Return interest names from the session graph."""
    result = g.query("MATCH (i:Interest) RETURN i.name")
    return [r[0] for r in result.result_set]
