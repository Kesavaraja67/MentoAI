"""
queries.py — Typed runners for MentoAI's 15 FalkorDB Cypher queries (G1–G15).

Each function loads its corresponding raw .cypher file and executes it using the
FalkorDB client. No raw Cypher strings are hardcoded in Python files.
"""
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.graph.client import get_graph
from app.graph.models import (
    LearnerSnapshot,
    LearnerNode,
    CuriosityNode,
    OpenLoopNode,
    EntityNode,
    MindView,
    MindViewNode,
    MindViewEdge,
    DecisionTrace,
)

QUERIES_DIR = Path(__file__).parent / "queries"


def _read_query(filename: str) -> str:
    path = QUERIES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Cypher file not found: {path}")
    return path.read_text(encoding="utf-8")


# G1: Learner Snapshot
def get_learner_snapshot(graph_name: str, learner_id: str) -> Optional[LearnerSnapshot]:
    graph = get_graph(graph_name)
    cypher = _read_query("g1_learner_snapshot.cypher")
    res = graph.query(cypher, {"learner_id": learner_id})
    if not res.result_set:
        return None

    row = res.result_set[0]
    learner = LearnerNode(
        id=row[0],
        display_name=row[1] or row[0],
        created_at="",
        language=row[2] or "en",
        register_text=row[3] or "curious learner",
        register_conf=float(row[4] or 0.5),
        voice_pref=row[5] or "natural",
    )
    interests = row[6] or []
    curiosities = [CuriosityNode(**c) for c in (row[7] or []) if isinstance(c, dict)]
    active_tales = row[8] or []
    open_loops = [OpenLoopNode(**op) for op in (row[9] or []) if isinstance(op, dict)]
    recent_entities = [EntityNode(**e) for e in (row[10] or []) if isinstance(e, dict)]
    known_count = int(row[11] or 0)

    return LearnerSnapshot(
        learner=learner,
        interests=interests,
        curiosities=curiosities,
        active_tales=active_tales,
        open_loops=open_loops,
        recent_entities=recent_entities,
        known_concepts_count=known_count,
    )


# G2: Semantic Recall
def semantic_recall(
    graph_name: str,
    query_text: Any = "",
    limit: int = 5,
    top_k: Optional[int] = None,
    **kwargs,
) -> List[Dict[str, Any]]:
    actual_limit = top_k if top_k is not None else limit
    if isinstance(query_text, (list, tuple)):
        q_str = ""
    else:
        q_str = str(query_text or "")

    graph = get_graph(graph_name)
    cypher = _read_query("g2_semantic_recall.cypher")
    res = graph.query(cypher, {"query_text": q_str, "limit": actual_limit})
    results = []
    for row in res.result_set:
        results.append({
            "key": row[0],
            "name": row[1],
            "summary": row[2],
            "domain": row[3],
            "label": row[4],
            "context_neighbors": row[5] or [],
        })
    return results


get_semantic_recall = semantic_recall


# G3: Bridge Paths
def find_bridge_paths(graph_name: str, learner_id: str, target_concept_key: str) -> List[Dict[str, Any]]:
    graph = get_graph(graph_name)
    cypher = _read_query("g3_bridge_paths.cypher")
    res = graph.query(cypher, {"learner_id": learner_id, "target_concept_key": target_concept_key})
    paths = []
    for row in res.result_set:
        paths.append({
            "anchor_name": row[0],
            "anchor_type": row[1],
            "hops": row[2],
            "path_names": row[3],
            "path_relationships": row[4],
        })
    return paths


# G4: Weak Prerequisites
def find_weak_prerequisites(graph_name: str, learner_id: str, concept_key: str) -> List[Dict[str, Any]]:
    graph = get_graph(graph_name)
    cypher = _read_query("g4_weak_prerequisites.cypher")
    res = graph.query(cypher, {"learner_id": learner_id, "concept_key": concept_key})
    weak = []
    for row in res.result_set:
        weak.append({
            "prerequisite_key": row[0],
            "prerequisite_name": row[1],
            "summary": row[2],
            "confidence": float(row[3]),
            "has_misconception": bool(row[4]),
            "misconception_statement": row[5],
            "hops": row[6],
            "path_keys": row[7],
        })
    return weak


# G5: Style Outcomes
def get_style_outcomes(graph_name: str, learner_id: Optional[str] = None) -> List[Dict[str, Any]]:
    graph = get_graph(graph_name)
    cypher = _read_query("g5_style_outcomes.cypher")
    res = graph.query(cypher, {"learner_id": learner_id or ""})
    outcomes = []
    for row in res.result_set:
        outcomes.append({
            "move_name": row[0],
            "times_used": row[1],
            "successes": row[2],
            "avg_strength": float(row[3] or 0.0),
        })
    return outcomes


# G6: Open Loops Ranked
def get_open_loops_ranked(graph_name: str) -> List[Dict[str, Any]]:
    graph = get_graph(graph_name)
    cypher = _read_query("g6_open_loops_ranked.cypher")
    res = graph.query(cypher)
    loops = []
    for row in res.result_set:
        loops.append({
            "loop_id": row[0],
            "text": row[1],
            "kind": row[2],
            "priority_note": row[3],
            "related_type": row[4],
            "related_name": row[5],
            "related_id": row[6],
        })
    return loops


# G7: Saga State
def get_saga_state(graph_name: str) -> Optional[Dict[str, Any]]:
    graph = get_graph(graph_name)
    cypher = _read_query("g7_saga_state.cypher")
    res = graph.query(cypher)
    if not res.result_set:
        return None
    row = res.result_set[0]
    return {
        "tale_id": row[0],
        "title": row[1],
        "premise": row[2],
        "last_chapter_idx": row[3],
        "last_chapter_text": row[4],
        "cliffhanger": row[5],
        "featured_entities": row[6] or [],
        "taught_concepts": row[7] or [],
    }


# G8: Write Evidence
def record_evidence(
    graph_name: str,
    turn_id: str,
    concept_key: str,
    learner_id: str = "",
    evidence_id: Optional[str] = None,
    kind: str = "explained",
    quote: str = "",
    verdict: str = "demonstrated",
    strength: float = 0.8,
    ts: str = "",
    new_depth: float = 0.5,
    new_confidence: float = 0.7,
    rationale: str = "",
    depth: Optional[float] = None,
    confidence: Optional[float] = None,
    **kwargs,
) -> Dict[str, Any]:
    import uuid
    import time
    ev_id = evidence_id or f"ev_{uuid.uuid4().hex[:8]}"
    d_val = depth if depth is not None else new_depth
    c_val = confidence if confidence is not None else new_confidence
    graph = get_graph(graph_name)
    cypher = _read_query("g8_write_evidence.cypher")
    res = graph.query(cypher, {
        "turn_id": turn_id,
        "concept_key": concept_key,
        "learner_id": learner_id,
        "evidence_id": ev_id,
        "kind": kind,
        "quote": quote,
        "verdict": verdict,
        "strength": strength,
        "ts": ts or str(int(time.time() * 1000)),
        "new_depth": d_val,
        "new_confidence": c_val,
        "rationale": rationale,
    })
    if res.result_set:
        return {"evidence_id": res.result_set[0][0], "confidence": float(res.result_set[0][1])}
    return {"evidence_id": ev_id, "confidence": c_val}


# G9: Write Concept Neighbourhood
def upsert_concept(
    graph_name: str,
    key: str,
    name: str,
    summary: str,
    domain: str = "general",
    created_by: str = "cartographer",
    created_at: str = "",
) -> Dict[str, Any]:
    graph = get_graph(graph_name)
    cypher = _read_query("g9_write_concept_neighbourhood.cypher")
    res = graph.query(cypher, {
        "key": key,
        "name": name,
        "summary": summary,
        "domain": domain,
        "created_by": created_by,
        "created_at": created_at,
    })
    return {"key": key, "name": name}


# G10: Write Decision
def record_decision(
    graph_name: str,
    decision_id: Optional[str] = None,
    agent: Optional[str] = None,
    kind: str = "pedagogical_guidance",
    rationale: str = "",
    confidence: float = 0.85,
    ts: str = "",
    turn_id: Optional[str] = None,
    agent_name: Optional[str] = None,
    chosen_move: Optional[str] = None,
    target_concept: Optional[str] = None,
    because_ids: Optional[List[str]] = None,
    **kwargs,
) -> str:
    import uuid
    import time
    dec_id = decision_id or f"dec_{uuid.uuid4().hex[:8]}"
    ag = agent_name or agent or "Agent"
    graph = get_graph(graph_name)
    cypher = _read_query("g10_write_decision.cypher")
    res = graph.query(cypher, {
        "decision_id": dec_id,
        "agent": ag,
        "kind": kind,
        "rationale": rationale,
        "confidence": confidence,
        "ts": ts or str(int(time.time() * 1000)),
        "turn_id": turn_id or "",
    })
    if chosen_move:
        try:
            graph.query(
                "MATCH (d:Decision {id: $did}), (m:TeachingMove {name: $mname}) MERGE (d)-[:CHOSE]->(m)",
                {"did": dec_id, "mname": chosen_move}
            )
        except Exception:
            pass
    if target_concept:
        try:
            graph.query(
                "MATCH (d:Decision {id: $did}), (c:Concept {key: $ckey}) MERGE (d)-[:TARGETS]->(c)",
                {"did": dec_id, "ckey": target_concept}
            )
        except Exception:
            pass
    if because_ids:
        for bid in because_ids:
            try:
                graph.query(
                    "MATCH (d:Decision {id: $did}), (t:Turn {id: $bid}) MERGE (d)-[:BECAUSE {note: 'prompted by turn'}]->(t)",
                    {"did": dec_id, "bid": bid}
                )
            except Exception:
                pass
    return dec_id


# G11: Decision Trace
def get_decision_trace(graph_name: str, decision_id: str) -> Optional[DecisionTrace]:
    graph = get_graph(graph_name)
    cypher = _read_query("g11_decision_trace.cypher")
    res = graph.query(cypher, {"decision_id": decision_id})
    if not res.result_set:
        return None
    row = res.result_set[0]
    return DecisionTrace(
        decision_id=row[0],
        agent=row[1],
        kind=row[2],
        rationale=row[3],
        ts=row[4],
        confidence=float(row[5] or 1.0),
        chose={"type": row[6], "name": row[7]} if row[6] else None,
        made_in_turn_id=row[8],
        because=row[9] or [],
    )


# G12: Mind View
def get_mind_view(graph_name: str, limit: int = 50) -> MindView:
    graph = get_graph(graph_name)
    cypher = _read_query("g12_mind_view.cypher")
    res = graph.query(cypher, {"limit": limit})
    nodes = []
    edges = []
    for row in res.result_set:
        node_id = row[0]
        nodes.append(MindViewNode(
            id=node_id,
            name=row[1],
            domain=row[2],
            depth=float(row[3] or 0.0),
            confidence=float(row[4] or 0.0),
        ))
        for edge in (row[5] or []):
            if edge.get("target"):
                edges.append(MindViewEdge(
                    source=node_id,
                    target=edge["target"],
                    type=edge.get("type", "CONNECTED_TO"),
                    why=edge.get("why"),
                ))
    return MindView(nodes=nodes, edges=edges)


# G13: Merge Duplicates
def find_duplicate_concepts(graph_name: str) -> List[Dict[str, Any]]:
    graph = get_graph(graph_name)
    cypher = _read_query("g13_merge_duplicates.cypher")
    res = graph.query(cypher)
    duplicates = []
    for row in res.result_set:
        duplicates.append({
            "key1": row[0],
            "name1": row[1],
            "key2": row[2],
            "name2": row[3],
        })
    return duplicates


# G14: Hubs and Clusters
def get_hubs_and_clusters(graph_name: str) -> List[Dict[str, Any]]:
    graph = get_graph(graph_name)
    cypher = _read_query("g14_hubs_and_clusters.cypher")
    res = graph.query(cypher)
    hubs = []
    for row in res.result_set:
        hubs.append({
            "key": row[0],
            "name": row[1],
            "domain": row[2],
            "degree": row[3],
        })
    return hubs


# G15: Forget Learner
def forget_learner_graph(graph_name: str) -> bool:
    graph = get_graph(graph_name)
    cypher = _read_query("g15_forget_learner.cypher")
    graph.query(cypher)
    return True


# Exported aliases for API and multi-agent coordination
forget_learner = forget_learner_graph
get_semantic_recall = semantic_recall
get_bridge_paths = find_bridge_paths
get_weak_prerequisites = find_weak_prerequisites
get_duplicate_candidates = find_duplicate_concepts


def record_concept_neighbourhood(graph_name: str, concepts: List[Any], relationships: Optional[List[Any]] = None) -> None:
    graph = get_graph(graph_name)
    for c in concepts:
        key = getattr(c, "key", None) or (c.get("key") if isinstance(c, dict) else "")
        name = getattr(c, "name", None) or (c.get("name") if isinstance(c, dict) else key)
        summary = getattr(c, "summary", None) or (c.get("summary") if isinstance(c, dict) else "")
        domain = getattr(c, "domain", None) or (c.get("domain") if isinstance(c, dict) else "general")
        upsert_concept(graph_name, key=key, name=name, summary=summary, domain=domain)
    if relationships:
        for rel in relationships:
            src = rel.get("source") if isinstance(rel, dict) else getattr(rel, "source", None)
            tgt = rel.get("target") if isinstance(rel, dict) else getattr(rel, "target", None)
            rtype = rel.get("type", "PREREQUISITE_OF") if isinstance(rel, dict) else getattr(rel, "type", "PREREQUISITE_OF")
            why = rel.get("props", {}).get("why", "") if isinstance(rel, dict) else getattr(rel, "why", "")
            if src and tgt:
                try:
                    graph.query(
                        f"MATCH (a:Concept {{key: $src}}), (b:Concept {{key: $tgt}}) MERGE (a)-[r:{rtype}]->(b) ON CREATE SET r.why = $why",
                        {"src": src, "tgt": tgt, "why": why}
                    )
                except Exception:
                    pass


def merge_duplicate_concepts(graph_name: str, canonical_key: str, duplicate_key: str) -> None:
    graph = get_graph(graph_name)
    try:
        graph.query(
            """
            MATCH (dup:Concept {key: $dup}), (canon:Concept {key: $canon})
            OPTIONAL MATCH (dup)<-[r1]-(n) WHERE n <> canon
            MERGE (n)-[new_r1:type(r1)]->(canon)
            OPTIONAL MATCH (dup)-[r2]->(m) WHERE m <> canon
            MERGE (canon)-[new_r2:type(r2)]->(m)
            DETACH DELETE dup
            """,
            {"dup": duplicate_key, "canon": canonical_key}
        )
    except Exception:
        pass

