from __future__ import annotations

from fastapi import FastAPI

from game_evidence_graph.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(title="Game Evidence Graph")
    app.include_router(router)
    return app
