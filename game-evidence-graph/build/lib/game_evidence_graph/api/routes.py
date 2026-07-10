from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import APIRouter

from game_evidence_graph.graph.evidence_graph_builder import build_evidence_graph
from game_evidence_graph.query.design_query_engine import DesignQueryEngine
from game_evidence_graph.schemas.query import DesignQuery

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/query/design")
def query_design(query: DesignQuery) -> dict:
    path = Path("data/processed/mechanic_intervention_dataset.csv")
    df = pd.read_csv(path) if path.exists() else pd.DataFrame()
    return DesignQueryEngine(df).query(query).model_dump(mode="json")


@router.get("/graph/summary")
def graph_summary() -> dict:
    path = Path("data/processed/mechanic_intervention_dataset.csv")
    if not path.exists():
        return {"nodes": 0, "edges": 0}
    graph = build_evidence_graph(pd.read_csv(path))
    return {"nodes": len(graph.nodes), "edges": len(graph.edges)}


@router.get("/datasets/mechanic-interventions")
def mechanic_interventions() -> list[dict]:
    path = Path("data/processed/mechanic_intervention_dataset.csv")
    return pd.read_csv(path).to_dict(orient="records") if path.exists() else []


@router.post("/ingest")
@router.post("/extract/studies")
@router.post("/build/game-ontology")
@router.post("/build/mechanic-interventions")
@router.post("/build/graph")
@router.get("/datasets/game-ontology")
@router.get("/datasets/study-ontology")
@router.get("/review/pending")
@router.post("/review/decision")
def not_yet_materialized() -> dict:
    return {"status": "available_via_cli", "message": "Endpoint is wired; use CLI service for local batch execution."}
