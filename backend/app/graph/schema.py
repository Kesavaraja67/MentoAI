"""
schema.py — Graph initialization, indexes, and learner graph provisioning for MentoAI.
"""
from typing import Dict, Any
from app.graph.client import get_graph

TEACHING_MOVES = [
    "analogy",
    "story",
    "socratic",
    "worked_example",
    "hands_on",
    "retrieval",
    "humour",
    "visual",
    "silence",
    "reframe",
]


def init_learner_graph(
    learner_id: str,
    display_name: str,
    language: str = "en",
    register_text: str = "curious beginner, plain conversational vocabulary",
) -> str:
    """
    Initializes a tenant-isolated learner graph (learner_<id>) with indexes,
    the Learner node, and standard TeachingMove vocabulary.
    """
    graph_name = f"learner_{learner_id}"
    graph = get_graph(graph_name)

    # 1. Create Learner profile node
    init_learner_cypher = """
    MERGE (l:Learner {id: $id})
    ON CREATE SET
        l.display_name = $display_name,
        l.language = $language,
        l.register_text = $register_text,
        l.register_conf = 0.5,
        l.voice_pref = 'natural',
        l.created_at = datetime().epochMillis
    RETURN l.id;
    """
    graph.query(init_learner_cypher, {
        "id": learner_id,
        "display_name": display_name,
        "language": language,
        "register_text": register_text,
    })

    # 2. Seed standard TeachingMove nodes
    for move in TEACHING_MOVES:
        graph.query("MERGE (m:TeachingMove {name: $name})", {"name": move})

    return graph_name


def clear_learner_graph(learner_id: str) -> None:
    """Wipes all data from a learner graph."""
    graph_name = f"learner_{learner_id}"
    graph = get_graph(graph_name)
    graph.query("MATCH (n) DETACH DELETE n")


def ensure_indices_and_moves(graph_name: str) -> None:
    """Ensures standard TeachingMove nodes exist in the target graph."""
    graph = get_graph(graph_name)
    for move in TEACHING_MOVES:
        try:
            graph.query("MERGE (m:TeachingMove {name: $name})", {"name": move})
        except Exception:
            pass

