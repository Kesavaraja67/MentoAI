"""
mind.py — Constellation mind-view graph endpoint for MentoAI.

Serves top active concepts and their semantic edges (G12) to power
the interactive visual knowledge graph.
"""
from typing import Dict, Any
from fastapi import APIRouter, Query

from app.graph.queries import get_mind_view
from app.api.websocket import is_graph_enabled

router = APIRouter(prefix="/api/learners", tags=["mind"])


@router.get("/{learner_id}/mind")
def get_learner_mind(learner_id: str, limit: int = Query(default=30, ge=5, le=100)) -> Dict[str, Any]:
    if not is_graph_enabled():
        # Graph Off proof mode
        return {"nodes": [], "edges": []}

    graph_name = f"learner_{learner_id}"
    mind = get_mind_view(graph_name, limit=limit)
    return mind.model_dump()
