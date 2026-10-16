"""
api/children.py — Endpoints for listing personas, inspecting child graph, and decision history.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.graph.client import get_graph
from app.graph.queries import q1_child_summary
from app.graph.seed import PERSONAS
from app.models import ChildSummary, GraphView, GraphNode, GraphEdge, DecisionOut

router = APIRouter(prefix="/api/children", tags=["children"])


@router.get("", response_model=list[ChildSummary])
def list_children() -> list[ChildSummary]:
    """List all synthetic personas with their summary from the child graphs."""
    summaries: list[ChildSummary] = []
    for p in PERSONAS:
        cid = p["id"]
        cg = get_graph(f"child_{cid}")
        summary_data = q1_child_summary(cg, cid)
        if summary_data:
            # Filter skills to those with confidence > 0 or top 4
            skills = [
                {"id": s["id"], "name": s["name"], "confidence": s["confidence"]}
                for s in summary_data.get("skills", [])
                if s["confidence"] > 0
            ]
            summaries.append(
                ChildSummary(
                    id=summary_data["child_id"],
                    name=summary_data["name"],
                    age=summary_data["age"],
                    interests=summary_data["interests"],
                    skills=skills,
                )
            )
        else:
            # Fallback directly to seed persona if graph not yet initialized
            summaries.append(
                ChildSummary(
                    id=p["id"],
                    name=p["name"],
                    age=p["age"],
                    interests=p["interests"],
                    skills=[
                        {"id": k, "name": k.replace("_", " ").title(), "confidence": v}
                        for k, v in p["confidences"].items()
                        if v > 0
                    ],
                )
            )
    return summaries


@router.get("/{child_id}/graph", response_model=GraphView)
def get_child_graph_view(child_id: str) -> GraphView:
    """Return all nodes and edges in the child_<child_id> long-term graph."""
    cg = get_graph(f"child_{child_id}")
    node_res = cg.query("MATCH (n) RETURN id(n), labels(n), properties(n)")
    edge_res = cg.query("MATCH (a)-[r]->(b) RETURN id(a), id(b), type(r), properties(r)")

    nodes: list[GraphNode] = []
    for row in node_res.result_set:
        nid, labels, props = row
        label = labels[0] if labels else "Unknown"
        node_id = props.get("id", str(nid))
        name = props.get("name", props.get("summary", node_id))
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


@router.get("/{child_id}/decisions", response_model=list[DecisionOut])
def get_child_decisions(child_id: str) -> list[DecisionOut]:
    """Return historical Decision nodes from the child_<child_id> graph."""
    cg = get_graph(f"child_{child_id}")
    res = cg.query(
        """
        MATCH (d:Decision)
        RETURN d.id, d.ts, d.kind, d.summary, d.memory_used
        ORDER BY d.ts DESC
        """
    )
    decisions: list[DecisionOut] = []
    for row in res.result_set:
        did, ts, kind, summary, mem_used = row
        decisions.append(
            DecisionOut(
                id=did,
                ts=ts or "",
                kind=kind or "",
                summary=summary or "",
                memory_used=mem_used or [],
            )
        )
    return decisions
