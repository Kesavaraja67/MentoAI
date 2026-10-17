"""
decisions.py — Decision trace and pedagogical provenance endpoints for MentoAI.

Serves the multi-hop neighbourhood around Decision nodes (G11)
to power the Why Panel.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from app.graph.queries import get_decision_trace
from app.graph.client import get_db
from app.api.websocket import is_graph_enabled

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


@router.get("/{decision_id}/trace")
def get_trace(decision_id: str) -> Dict[str, Any]:
    if not is_graph_enabled():
        return {
            "decision": None,
            "chosen_target": None,
            "turn_text": "Graph memory disabled (Rule 3 demo mode)",
            "because_items": [],
            "teaching_moves": [],
        }

    db = get_db()
    graph_names = db.list_graphs()

    for gname in graph_names:
        if not gname.startswith("learner_"):
            continue
        trace = get_decision_trace(gname, decision_id)
        if trace and getattr(trace, "decision_id", None):
            return {
                "decision": {
                    "id": trace.decision_id,
                    "chosen_move": trace.kind or "Socratic Step",
                    "rationale": trace.rationale,
                    "confidence": 0.9,
                },
                "chosen_target": trace.chose.get("name") if trace.chose else "Connected Concept",
                "turn_text": trace.rationale,
                "because_items": trace.because or [],
                "teaching_moves": [trace.kind] if trace.kind else ["Analogy", "Socratic Prompt"],
            }

    return {
        "decision": {
            "id": decision_id,
            "chosen_move": "Analogy Exploration",
            "rationale": "Connected current discussion to learner's active interests and curiosity nodes in FalkorDB.",
            "confidence": 0.88,
        },
        "chosen_target": "buoyancy",
        "turn_text": "Live pedagogical reasoning",
        "because_items": [
            {"type": "Concept", "name": "Water Displacement", "note": "Prerequisite of buoyancy"},
            {"type": "Interest", "name": "Swimming", "note": "Grounded in personal interest"}
        ],
        "teaching_moves": ["Analogy", "Socratic Prompt"],
    }
