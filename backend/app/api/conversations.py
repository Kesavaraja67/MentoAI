"""
conversations.py — Conversation lifecycle and turn history endpoints.
"""
import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.graph.client import get_graph

router = APIRouter(tags=["conversations"])


class StartConversationRequest(BaseModel):
    title: str = "New Conversation"


@router.post("/api/learners/{learner_id}/conversations", status_code=201)
def start_conversation(learner_id: str, payload: StartConversationRequest) -> Dict[str, Any]:
    graph_name = f"learner_{learner_id}"
    conv_id = f"conv_{uuid.uuid4().hex[:8]}"

    graph = get_graph(graph_name)
    res = graph.query(
        """
        MATCH (l:Learner {id: $lid})
        CREATE (c:Conversation {
            id: $cid,
            title: $title,
            started_at: timestamp(),
            status: 'active'
        })
        CREATE (l)-[:HAD]->(c)
        RETURN c.id
        """,
        {"lid": learner_id, "cid": conv_id, "title": payload.title},
    )

    if not res.result_set:
        raise HTTPException(status_code=404, detail="Learner not found")

    return {"conversation_id": conv_id, "learner_id": learner_id, "title": payload.title}


@router.get("/api/learners/{learner_id}/conversations")
def list_conversations(learner_id: str) -> List[Dict[str, Any]]:
    graph_name = f"learner_{learner_id}"
    graph = get_graph(graph_name)
    res = graph.query(
        """
        MATCH (l:Learner {id: $lid})-[:HAD]->(c:Conversation)
        RETURN c.id, c.title, c.started_at, c.ended_at, c.summary, c.mood_arc
        ORDER BY c.started_at DESC
        LIMIT 20
        """,
        {"lid": learner_id},
    )

    items = []
    for r in res.result_set:
        items.append({
            "id": r[0],
            "title": r[1] or "Conversation",
            "started_at": r[2],
            "ended_at": r[3],
            "summary": r[4] or "",
            "mood_arc": r[5] or "",
        })
    return items


@router.get("/api/conversations/{conversation_id}/turns")
def get_turns(conversation_id: str) -> List[Dict[str, Any]]:
    # Search across learner graphs or standard query
    # Find which graph has this conversation
    from app.graph.client import get_db
    db = get_db()
    graph_names = db.list_graphs()

    for gname in graph_names:
        if not gname.startswith("learner_"):
            continue
        graph = db.select_graph(gname)
        res = graph.query(
            """
            MATCH (c:Conversation {id: $cid})-[:HAS_TURN]->(t:Turn)
            RETURN t.id, t.role, t.text, t.ts
            ORDER BY t.ts ASC
            """,
            {"cid": conversation_id},
        )
        if res.result_set:
            return [
                {"id": r[0], "role": r[1], "text": r[2], "ts": r[3]}
                for r in res.result_set
            ]

    return []
