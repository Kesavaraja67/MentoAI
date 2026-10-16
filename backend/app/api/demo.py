"""
api/demo.py — Demo reset endpoint.

Re-seeds all three personas and cleans up all active session graphs.
"""
from __future__ import annotations

from fastapi import APIRouter
from app.graph.client import get_db, delete_graph
from app.graph.schema import seed_curriculum, build_child_graph
from app.graph.seed import PERSONAS
from app.models import ResetResponse

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/reset", response_model=ResetResponse)
def reset_demo() -> ResetResponse:
    """
    Re-seed the curriculum and all three synthetic personas.
    Deletes all existing session_* graphs so the demo starts in a clean state.
    """
    seed_curriculum()

    # Re-build each child graph
    seeded: list[str] = []
    for p in PERSONAS:
        cid = p["id"]
        build_child_graph(cid)
        seeded.append(cid)

    # Clean up any leftover session_* graphs
    try:
        db = get_db()
        keys = db.connection.keys("session_*")
        for k in keys:
            k_str = k.decode("utf-8") if isinstance(k, bytes) else str(k)
            graph_id = k_str.split(":")[-1] if ":" in k_str else k_str
            delete_graph(graph_id)
    except Exception:
        pass

    return ResetResponse(status="ok", personas_seeded=seeded)
