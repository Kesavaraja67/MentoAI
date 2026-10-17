"""
admin.py — Administrative and Hackathon Rule 3 Graph Off toggle.
"""
from typing import Dict, Any
from fastapi import APIRouter
from pydantic import BaseModel

from app.api.websocket import is_graph_enabled, set_graph_mode

router = APIRouter(prefix="/api/admin", tags=["admin"])


class GraphModePayload(BaseModel):
    enabled: bool


@router.get("/graph-mode")
def get_graph_mode() -> Dict[str, Any]:
    return {"graph_mode_enabled": is_graph_enabled()}


@router.post("/graph-mode")
def update_graph_mode(payload: GraphModePayload) -> Dict[str, Any]:
    """
    Hackathon Rule 3 Proof:
    Toggles FalkorDB graph memory on or off dynamically to prove that MentoAI's
    callbacks, bridging, and pedagogical traces depend directly on the graph.
    """
    set_graph_mode(payload.enabled)
    return {
        "status": "updated",
        "graph_mode_enabled": is_graph_enabled(),
        "detail": "Graph memory active" if payload.enabled else "Graph memory bypassed (Rule 3 test double)",
    }


@router.get("/llm-test")
def test_llm() -> Dict[str, Any]:
    import os
    import httpx
    groq_key = os.getenv("LLM_API_KEY", "")
    model = os.getenv("LLM_MODEL", "qwen/qwen3.8-27b")
    
    result = {"model": model, "status": "unknown"}
    if groq_key:
        try:
            with httpx.Client(timeout=6.0) as client:
                test_chat = client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={"model": model, "messages": [{"role": "user", "content": "hello"}], "max_tokens": 15}
                )
                if test_chat.status_code == 200:
                    result["status"] = "ok"
                    result["reply"] = test_chat.json()["choices"][0]["message"]["content"]
                else:
                    result["status"] = f"HTTP {test_chat.status_code}"
                    result["detail"] = test_chat.text
        except Exception as ex:
            result["status"] = "error"
            result["detail"] = str(ex)
    return result
