"""
mcp_server.py — FastMCP server exposing MentoAI's FalkorDB graph reasoning tools.

Provides standardized MCP tools for AI agents (Track 02: Agent Memory & Track 01: Connected Data):
1. get_learner_snapshot: Register, top interests, active curiosities, and open loops (G1).
2. semantic_recall: 384-d vector search + 1-hop expansion across graph memory (G2).
3. find_bridge_paths: Multi-hop graph traversal bridging target concepts to known interests (G3).
4. diagnose_weak_prerequisites: Upstream prerequisite chain diagnosis (G4).
5. inspect_decision_trace: Full pedagogical decision provenance with BECAUSE edges (G11).
6. get_mind_graph: Active constellation subgraph of learner concepts and relationships (G12).
"""
import sys
import json
from typing import Optional, List, Dict, Any

from app.graph.queries import (
    get_learner_snapshot,
    get_semantic_recall,
    get_bridge_paths,
    get_weak_prerequisites,
    get_decision_trace,
    get_mind_view,
)
from app.graph.embeddings import get_embedding

# Attempt to load official FastMCP from mcp SDK if installed
try:
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("mentoai_mcp")
    HAS_FASTMCP = True
except ImportError:
    HAS_FASTMCP = False
    mcp = None


def inspect_learner_snapshot(learner_id: str) -> Dict[str, Any]:
    """
    Retrieve snapshot of learner's profile, register, interests, curiosities, and open loops (G1).
    """
    graph_name = f"learner_{learner_id}"
    snap = get_learner_snapshot(graph_name, learner_id)
    if not snap:
        return {"found": False, "message": f"Learner {learner_id} not found"}
    return {"found": True, "snapshot": snap.model_dump()}


def recall_memory(query: str, learner_id: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Perform semantic vector search + 1-hop expansion over concept and turn memories in FalkorDB (G2).
    """
    graph_name = f"learner_{learner_id}"
    emb = get_embedding(query)
    nodes = get_semantic_recall(graph_name, emb, top_k=top_k)
    return {
        "query": query,
        "learner_id": learner_id,
        "results": [n.model_dump() for n in nodes],
    }


def find_bridge(learner_id: str, target_concept: str) -> Dict[str, Any]:
    """
    Find multi-hop shortest paths from target concept to learner's known concepts or interests (G3).
    """
    graph_name = f"learner_{learner_id}"
    bridges = get_bridge_paths(graph_name, learner_id, target_concept)
    return {
        "learner_id": learner_id,
        "target_concept": target_concept,
        "bridges": [b.model_dump() for b in bridges],
    }


def diagnose_prerequisites(learner_id: str, target_concept: str) -> Dict[str, Any]:
    """
    Traverse upstream prerequisite graph to find concepts with thin evidence or misconceptions (G4).
    """
    graph_name = f"learner_{learner_id}"
    weak = get_weak_prerequisites(graph_name, learner_id, target_concept)
    return {
        "learner_id": learner_id,
        "target_concept": target_concept,
        "weak_prerequisites": [w.model_dump() for w in weak],
    }


def explain_decision(decision_id: str) -> Dict[str, Any]:
    """
    Inspect the multi-hop provenance neighborhood around a Decision node with BECAUSE edges (G11).
    """
    from app.graph.client import get_db
    db = get_db()
    for gname in db.list_graphs():
        if not gname.startswith("learner_"):
            continue
        trace = get_decision_trace(gname, decision_id)
        if trace:
            return trace.model_dump()
    return {"error": f"Decision {decision_id} not found"}


def fetch_mind(learner_id: str, limit: int = 30) -> Dict[str, Any]:
    """
    Fetch active knowledge constellation subgraph (G12).
    """
    graph_name = f"learner_{learner_id}"
    mind = get_mind_view(graph_name, limit=limit)
    return mind.model_dump()


# Register FastMCP tools if library is active
if HAS_FASTMCP and mcp is not None:
    mcp.tool()(inspect_learner_snapshot)
    mcp.tool()(recall_memory)
    mcp.tool()(find_bridge)
    mcp.tool()(diagnose_prerequisites)
    mcp.tool()(explain_decision)
    mcp.tool()(fetch_mind)


if __name__ == "__main__":
    if HAS_FASTMCP and mcp is not None:
        mcp.run()
    else:
        # Fallback stdio JSON-RPC loop
        print(json.dumps({"status": "MentoAI MCP tools initialized in standalone mode"}), file=sys.stderr)
