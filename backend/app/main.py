"""
main.py — FastAPI application entry point.

Only the health endpoint lives here in Phase 0.
All other routes are registered by their router modules in app/api/.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.graph.client import ping

settings = get_settings()

app = FastAPI(
    title="MentoAI API",
    description="Voice-first lifelong companion learning engine backed by FalkorDB graph memory.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from app.api import learners, conversations, mind, decisions, digest, personas, admin, websocket

app.include_router(learners.router)
app.include_router(conversations.router)
app.include_router(mind.router)
app.include_router(decisions.router)
app.include_router(digest.router)
app.include_router(personas.router)
app.include_router(admin.router)
app.include_router(websocket.router)


@app.get("/api/health", tags=["health"])
def health() -> dict:
    """
    Returns {"status": "ok"} when backend and FalkorDB are both reachable.
    Returns {"status": "degraded", "detail": "..."} if FalkorDB is down.
    Used by the smoke check and Docker healthcheck.
    """
    db_ok = ping()
    if db_ok:
        return {"status": "ok", "falkordb": "ok"}
    return {"status": "degraded", "falkordb": "unreachable"}
