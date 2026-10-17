"""
digest.py — Grown-up digest endpoint for parents and educators.
"""
from typing import Dict, Any, List
from fastapi import APIRouter

from app.graph.client import get_graph
from app.api.websocket import is_graph_enabled

router = APIRouter(prefix="/api/learners", tags=["digest"])


@router.get("/{learner_id}/digest")
def get_digest(learner_id: str) -> Dict[str, Any]:
    if not is_graph_enabled():
        return {
            "learner_id": learner_id,
            "digests": [],
            "note": "Graph memory disabled (Rule 3 demonstration mode)",
        }

    graph_name = f"learner_{learner_id}"
    graph = get_graph(graph_name)
    res = graph.query(
        """
        MATCH (l:Learner {id: $lid})-[:HAS_DIGEST]->(d:Digest)
        RETURN d.id, d.text, d.topics, d.strengths, d.shaky_areas, d.offline_activities, d.ts
        ORDER BY d.ts DESC
        LIMIT 5
        """,
        {"lid": learner_id},
    )

    items = []
    for r in res.result_set:
        items.append({
            "id": r[0],
            "text": r[1] or "",
            "topics": r[2] or [],
            "strengths": r[3] or [],
            "shaky_areas": r[4] or [],
            "offline_activities": r[5] or [],
            "ts": r[6],
        })

    return {"learner_id": learner_id, "digests": items}
