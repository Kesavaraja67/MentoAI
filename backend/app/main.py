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
    title="Primer API",
    description="Adaptive arithmetic tutor backed by FalkorDB graph memory.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


from app.api import children, sessions, graphview, demo

app.include_router(children.router)
app.include_router(sessions.router)
app.include_router(graphview.router)
app.include_router(demo.router)


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
