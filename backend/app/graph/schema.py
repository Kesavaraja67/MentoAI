"""
graph/schema.py — Functions that create and populate FalkorDB graphs.

Three operations:
  1. seed_curriculum()   — create/refresh the `curriculum` template graph.
  2. build_child_graph() — copy curriculum into `child_<id>`, add persona data.
  3. build_session_graph() — copy working state into `session_<id>`.

All queries in this file are also saved as .cypher files in graph/queries/
for documentation purposes. The .cypher files are the canonical query text;
this module reads them at runtime.

IMPORTANT: Every query here was validated against a real FalkorDB container.
Fixes from that validation are recorded in docs/QUERIES.md.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import falkordb

from app.graph.client import get_graph, delete_graph
from app.graph.seed import (
    SKILLS,
    MISCONCEPTIONS,
    HINT_STYLES,
    PERSONAS,
    get_confidence,
)


# ── 1. Seed the curriculum template graph ────────────────────────────────────

def seed_curriculum() -> None:
    """
    Write the 13 Skill nodes, prerequisite edges, and Misconception nodes
    into the `curriculum` graph. Idempotent: deletes and recreates.
    """
    # Delete and recreate so seed is always clean.
    delete_graph("curriculum")
    g = get_graph("curriculum")

    # Create Skill nodes
    for skill in SKILLS:
        g.query(
            "CREATE (:Skill {id: $id, name: $name, order: $order})",
            {"id": skill["id"], "name": skill["name"], "order": skill["order"]},
        )

    # Create PREREQUISITE_OF edges: (prereq)-[:PREREQUISITE_OF]->(skill)
    for skill in SKILLS:
        for prereq_id in skill["prereqs"]:
            g.query(
                """
                MATCH (prereq:Skill {id: $prereq_id}),
                      (skill:Skill  {id: $skill_id})
                CREATE (prereq)-[:PREREQUISITE_OF]->(skill)
                """,
                {"prereq_id": prereq_id, "skill_id": skill["id"]},
            )

    # Create Misconception nodes and INDICATES_WEAK edges
    for m in MISCONCEPTIONS:
        g.query(
            "CREATE (:Misconception {id: $id, name: $name})",
            {"id": m["id"], "name": m["name"]},
        )
        g.query(
            """
            MATCH (m:Misconception {id: $mid}),
                  (s:Skill         {id: $sid})
            CREATE (m)-[:INDICATES_WEAK]->(s)
            """,
            {"mid": m["id"], "sid": m["indicates"]},
        )


# ── 2. Build a child graph ───────────────────────────────────────────────────

def build_child_graph(persona_id: str) -> None:
    """
    Create `child_<persona_id>` from scratch:
      - Copy Skill DAG from curriculum (with persona confidences).
      - Copy Misconception nodes and INDICATES_WEAK edges.
      - Add Child node, Interest nodes, HintStyle nodes with defaults.
    """
    persona = next(p for p in PERSONAS if p["id"] == persona_id)
    graph_name = f"child_{persona_id}"
    delete_graph(graph_name)
    g = get_graph(graph_name)

    # Child node
    g.query(
        "CREATE (:Child {id: $id, name: $name, age: $age})",
        {"id": persona["id"], "name": persona["name"], "age": persona["age"]},
    )

    # Skill nodes with persona confidences
    for skill in SKILLS:
        confidence = get_confidence(persona, skill["id"])
        g.query(
            """
            CREATE (:Skill {
                id: $id,
                name: $name,
                order: $order,
                confidence: $confidence,
                attempts: 0,
                last_seen: ''
            })
            """,
            {
                "id": skill["id"],
                "name": skill["name"],
                "order": skill["order"],
                "confidence": confidence,
            },
        )

    # PREREQUISITE_OF edges
    for skill in SKILLS:
        for prereq_id in skill["prereqs"]:
            g.query(
                """
                MATCH (prereq:Skill {id: $prereq_id}),
                      (skill:Skill  {id: $skill_id})
                CREATE (prereq)-[:PREREQUISITE_OF]->(skill)
                """,
                {"prereq_id": prereq_id, "skill_id": skill["id"]},
            )

    # Misconception nodes and INDICATES_WEAK edges
    for m in MISCONCEPTIONS:
        g.query(
            "CREATE (:Misconception {id: $id, name: $name})",
            {"id": m["id"], "name": m["name"]},
        )
        g.query(
            """
            MATCH (m:Misconception {id: $mid}),
                  (s:Skill         {id: $sid})
            CREATE (m)-[:INDICATES_WEAK]->(s)
            """,
            {"mid": m["id"], "sid": m["indicates"]},
        )

    # Interest nodes
    for interest in persona["interests"]:
        g.query(
            """
            MATCH (c:Child {id: $cid})
            CREATE (i:Interest {name: $name})
            CREATE (c)-[:INTERESTED_IN {weight: 1.0}]->(i)
            """,
            {"cid": persona["id"], "name": interest},
        )

    # HintStyle nodes — defaults for this child
    for hs in HINT_STYLES:
        g.query(
            "CREATE (:HintStyle {id: $id, order: $order, score: $score, tries: $tries})",
            {"id": hs["id"], "order": hs["order"], "score": hs["score"], "tries": hs["tries"]},
        )


# ── 3. Build a session graph (hydrate) ───────────────────────────────────────

def build_session_graph(
    session_id: str,
    child_id: str,
    graph_mode: str,
    target_skill_id: str,
    origin_skill_id: str,
) -> None:
    """
    Create `session_<session_id>`:
      - Session node.
      - Working copies of Skill nodes (with current confidences from child graph).
      - PREREQUISITE_OF edges.
      - Misconception + INDICATES_WEAK.
      - HintStyle copies.
      - Interest copies.
    When graph_mode == 'off', creates only a bare Session node.
    """
    graph_name = f"session_{session_id}"
    delete_graph(graph_name)
    g = get_graph(graph_name)
    now = _now()

    # Session node
    g.query(
        """
        CREATE (:Session {
            id: $id,
            child_id: $child_id,
            started_at: $started_at,
            graph_mode: $graph_mode,
            turn_count: 0,
            target_skill: $target_skill,
            origin_skill: $origin_skill
        })
        """,
        {
            "id": session_id,
            "child_id": child_id,
            "started_at": now,
            "graph_mode": graph_mode,
            "target_skill": target_skill_id,
            "origin_skill": origin_skill_id,
        },
    )

    if graph_mode == "off":
        return  # bare session only

    child_g = get_graph(f"child_{child_id}")

    # Copy Skill nodes with current confidences
    result = child_g.query(
        "MATCH (s:Skill) RETURN s.id, s.name, s.order, s.confidence, s.attempts, s.last_seen"
    )
    for row in result.result_set:
        sid, sname, sorder, sconf, sattempts, slast = row
        g.query(
            """
            CREATE (:Skill {
                id: $id,
                name: $name,
                order: $order,
                confidence: $confidence,
                attempts: $attempts,
                last_seen: $last_seen
            })
            """,
            {
                "id": sid,
                "name": sname,
                "order": sorder,
                "confidence": sconf,
                "attempts": sattempts,
                "last_seen": slast,
            },
        )

    # Re-create PREREQUISITE_OF edges in session graph
    for skill in SKILLS:
        for prereq_id in skill["prereqs"]:
            g.query(
                """
                MATCH (prereq:Skill {id: $prereq_id}),
                      (skill:Skill  {id: $skill_id})
                CREATE (prereq)-[:PREREQUISITE_OF]->(skill)
                """,
                {"prereq_id": prereq_id, "skill_id": skill["id"]},
            )

    # Copy Misconceptions
    result = child_g.query("MATCH (m:Misconception) RETURN m.id, m.name")
    for row in result.result_set:
        mid, mname = row
        g.query(
            "CREATE (:Misconception {id: $id, name: $name})",
            {"id": mid, "name": mname},
        )
    for m in MISCONCEPTIONS:
        g.query(
            """
            MATCH (m:Misconception {id: $mid}),
                  (s:Skill         {id: $sid})
            CREATE (m)-[:INDICATES_WEAK]->(s)
            """,
            {"mid": m["id"], "sid": m["indicates"]},
        )

    # Copy HintStyles
    result = child_g.query("MATCH (h:HintStyle) RETURN h.id, h.order, h.score, h.tries")
    for row in result.result_set:
        hid, horder, hscore, htries = row
        g.query(
            "CREATE (:HintStyle {id: $id, order: $order, score: $score, tries: $tries})",
            {"id": hid, "order": horder, "score": hscore, "tries": htries},
        )

    # Copy Interests
    result = child_g.query(
        "MATCH (:Child)-[r:INTERESTED_IN]->(i:Interest) RETURN i.name, r.weight"
    )
    for row in result.result_set:
        iname, iweight = row
        g.query(
            "CREATE (:Interest {name: $name})",
            {"name": iname},
        )


# ── Utility ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_session_id() -> str:
    return str(uuid.uuid4())
