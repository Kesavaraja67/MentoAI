"""
api/graphview.py — Endpoints for decision justification subgraph and session graph visualization.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.graph.client import get_graph
from app.graph.queries import q8_decision_path
from app.graph.seed import PERSONAS
from app.models import GraphView, GraphNode, GraphEdge

router = APIRouter(tags=["graphview"])


@router.get("/api/sessions/{session_id}/graph", response_model=GraphView)
def get_session_graph_view(session_id: str) -> GraphView:
    """Return nodes and edges of the transient session graph for the Why panel canvas."""
    sg = get_graph(f"session_{session_id}")
    node_res = sg.query("MATCH (n) RETURN id(n), labels(n), properties(n)")
    edge_res = sg.query("MATCH (a)-[r]->(b) RETURN id(a), id(b), type(r), properties(r)")

    nodes: list[GraphNode] = []
    for row in node_res.result_set:
        nid, labels, props = row
        label = labels[0] if labels else "Unknown"
        node_id = props.get("id", str(nid))
        name = props.get("name", props.get("summary", props.get("id", str(nid))))
        nodes.append(
            GraphNode(
                id=str(node_id),
                label=str(name),
                kind=label,
                properties=props,
            )
        )

    edges: list[GraphEdge] = []
    for row in edge_res.result_set:
        src_id, tgt_id, rel_type, props = row
        edges.append(
            GraphEdge(
                source=str(src_id),
                target=str(tgt_id),
                label=rel_type,
                properties=props,
            )
        )

    return GraphView(nodes=nodes, edges=edges)


@router.get("/api/decisions/{decision_id}/path")
def get_decision_justification_path(decision_id: str, session_id: str = "") -> dict:
    """
    Return nodes and edges that justify one Decision node.
    Checks the session graph first (if active), then searches child graphs.
    Used by the Why panel to highlight the provenance subgraph.
    """
    rows = []
    # 1. Try session graph
    if session_id:
        sg = get_graph(f"session_{session_id}")
        rows = q8_decision_path(sg, decision_id)

    # 2. Try each child graph if not found in session
    if not rows:
        for p in PERSONAS:
            cg = get_graph(f"child_{p['id']}")
            rows = q8_decision_path(cg, decision_id)
            if rows:
                break

    if not rows:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")

    first = rows[0]
    because_list = []
    seen_because = set()
    for r in rows:
        bid = r.get("because_id")
        if bid and bid not in seen_because:
            seen_because.add(bid)
            because_list.append({
                "id": bid,
                "label": r.get("because_label"),
                "role": r.get("because_role"),
            })

    return {
        "decision_id": first["decision_id"],
        "kind": first["kind"],
        "summary": first["summary"],
        "memory_used": first["memory_used"],
        "chose": {"id": first["chose_id"], "label": first["chose_label"]} if first.get("chose_id") else None,
        "because": because_list,
    }
