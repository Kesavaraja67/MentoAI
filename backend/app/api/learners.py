"""
learners.py — Learner management and privacy endpoints for MentoAI.

Implements registration, profile retrieval (G1), and one-click graph erasure (G15).
"""
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.graph.client import get_graph
from app.graph.schema import ensure_indices_and_moves
from app.graph.queries import get_learner_snapshot, forget_learner

router = APIRouter(prefix="/api/learners", tags=["learners"])


class CreateLearnerRequest(BaseModel):
    display_name: str
    language: str = "en"
    register_text: str = "curious learner"
    voice_pref: str = "natural"


@router.post("", status_code=201)
def create_learner(payload: CreateLearnerRequest) -> Dict[str, Any]:
    learner_id = f"lrn_{uuid.uuid4().hex[:8]}"
    graph_name = f"learner_{learner_id}"

    # Initialize graph schema, vector indices, and teaching moves
    ensure_indices_and_moves(graph_name)

    graph = get_graph(graph_name)
    graph.query(
        """
        CREATE (l:Learner {
            id: $id,
            display_name: $name,
            language: $lang,
            register_text: $reg,
            register_conf: 0.8,
            voice_pref: $voice,
            created_at: timestamp()
        })
        RETURN l.id
        """,
        {
            "id": learner_id,
            "name": payload.display_name,
            "lang": payload.language,
            "reg": payload.register_text,
            "voice": payload.voice_pref,
        },
    )

    return {"learner_id": learner_id, "display_name": payload.display_name, "graph_name": graph_name}


@router.get("/{learner_id}")
def get_learner(learner_id: str) -> Dict[str, Any]:
    graph_name = f"learner_{learner_id}"
    snapshot = get_learner_snapshot(graph_name, learner_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Learner {learner_id} not found")
    return snapshot.model_dump()


@router.post("/{learner_id}/forget")
def forget_learner_endpoint(learner_id: str) -> Dict[str, Any]:
    """
    Hackathon Rule 6 compliance: Complete, irreversible deletion of learner's graph memory.
    """
    graph_name = f"learner_{learner_id}"
    ok = forget_learner(graph_name)
    return {"status": "forgotten", "learner_id": learner_id, "graph_deleted": ok}
