from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import typer
from dotenv import load_dotenv
from rich.console import Console

from game_evidence_graph.datasets.completeness_report import build_completeness_report, write_audit_report
from game_evidence_graph.datasets.exporters import write_csv, write_json, write_jsonl
from game_evidence_graph.datasets.game_ontology_builder import build_game_ontology
from game_evidence_graph.datasets.mechanic_intervention_builder import build_dataset_c
from game_evidence_graph.datasets.study_ontology_builder import load_study_ontology
from game_evidence_graph.datasets.validators import (
    validate_dataset_c,
    validate_game_ontology,
    validate_study_ontology,
)
from game_evidence_graph.evaluation.graph_metrics import graph_edge_metrics
from game_evidence_graph.extraction.study_extractor import extract_study_ontology
from game_evidence_graph.graph.evidence_graph_builder import build_evidence_graph
from game_evidence_graph.graph.export_graphml import export_graphml
from game_evidence_graph.ingestion.pdf_loader import ingest_pdf_folder
from game_evidence_graph.llm.base import LLMClient
from game_evidence_graph.llm.mock_client import MockLLMClient
from game_evidence_graph.llm.openai_client import OpenAIClient
from game_evidence_graph.query.design_query_engine import DesignQueryEngine
from game_evidence_graph.recite_adapter.adaptation_report import write_adaptation_report
from game_evidence_graph.recite_adapter.inspect_repo import inspect_repo
from game_evidence_graph.review.review_queue import build_review_queue, export_review_csv, write_review_jsonl
from game_evidence_graph.schemas.game import GameOntology
from game_evidence_graph.schemas.query import DesignQuery
from game_evidence_graph.schemas.study import StudyOntology

app = typer.Typer(help="Build literature-derived game intervention evidence graphs.")
review_app = typer.Typer(help="Human review queue commands.")
recite_app = typer.Typer(help="ReCITE/ReVITE adaptation commands.")
eval_app = typer.Typer(help="Evaluation commands.")
app.add_typer(review_app, name="review")
app.add_typer(recite_app, name="recite")
app.add_typer(eval_app, name="eval")
console = Console()


def get_llm_client() -> LLMClient:
    load_dotenv(override=True)
    provider = os.getenv("GAME_EVIDENCE_LLM_PROVIDER", "mock").strip().lower()
    model = os.getenv("GAME_EVIDENCE_LLM_MODEL", "gpt-5-mini").strip()

    if provider in {"", "mock"}:
        return MockLLMClient()
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise typer.BadParameter("OPENAI_API_KEY is required when GAME_EVIDENCE_LLM_PROVIDER=openai.")
        return OpenAIClient(model=model, api_key=api_key)
    raise typer.BadParameter(f"Unsupported GAME_EVIDENCE_LLM_PROVIDER: {provider}")


def _ensure_project_dirs() -> None:
    for path in [
        "data/input/papers",
        "data/intermediate",
        "data/processed",
        "data/gold",
        "data/review",
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)


@app.command()
def init() -> None:
    _ensure_project_dirs()
    console.print("Initialized Game Evidence Graph data directories.")


@app.command()
def ingest(pdf_dir: Path = Path("data/input/papers"), out: Path = Path("data/intermediate")) -> None:
    docs = ingest_pdf_folder(pdf_dir, out)
    console.print(f"Ingested {len(docs)} PDFs.")


@app.command("extract-studies")
def extract_studies(
    intermediate: Path = Path("data/intermediate"),
    out: Path = Path("data/processed/study_ontology.json"),
) -> None:
    # The production interface is LLM-backed; the default mock yields empty extractions.
    papers = []
    for folder in sorted(p for p in intermediate.glob("paper_*") if p.is_dir()):
        metadata_path = folder / "metadata.json"
        pages_path = folder / "pages.json"
        if metadata_path.exists() and pages_path.exists():
            from game_evidence_graph.schemas.paper import PaperDocument

            papers.append(PaperDocument.model_validate_json(pages_path.read_text()))
    ontology = asyncio.run(extract_study_ontology(get_llm_client(), papers))
    write_json(out, ontology)
    console.print(f"Wrote {len(ontology.studies)} study records to {out}.")


@app.command("build-game-ontology")
def build_game_ontology_cmd(
    studies: Path = Path("data/processed/study_ontology.json"),
    seed: Optional[Path] = Path("data/input/seed_game_ontology.json"),
    out: Path = Path("data/processed/game_ontology.json"),
) -> None:
    ontology = build_game_ontology(load_study_ontology(studies), seed if seed and seed.exists() else None)
    write_json(out, ontology)
    console.print(f"Wrote {len(ontology.games)} game records to {out}.")


@app.command("build-mechanic-interventions")
def build_mechanic_interventions(
    studies: Path = Path("data/processed/study_ontology.json"),
    games: Path = Path("data/processed/game_ontology.json"),
    out: Path = Path("data/processed/mechanic_intervention_dataset.csv"),
) -> None:
    study_ontology = load_study_ontology(studies)
    game_ontology = GameOntology.model_validate_json(games.read_text()) if games.exists() else GameOntology()
    df = build_dataset_c(study_ontology, game_ontology)
    write_csv(out, df)
    write_jsonl(out.with_suffix(".jsonl"), df.to_dict(orient="records"))
    console.print(f"Wrote {len(df)} Dataset C rows to {out}.")


@app.command("build-graph")
def build_graph(
    dataset_c: Path = Path("data/processed/mechanic_intervention_dataset.csv"),
    out: Path = Path("data/processed/causal_claim_graph.json"),
) -> None:
    df = pd.read_csv(dataset_c) if dataset_c.exists() else pd.DataFrame()
    graph = build_evidence_graph(df) if not df.empty else build_evidence_graph(pd.DataFrame(columns=[]))
    write_json(out, graph)
    export_graphml(graph, out.with_suffix(".graphml"))
    edge_df = pd.DataFrame([edge.model_dump(mode="json") for edge in graph.edges])
    write_csv(out.parent / "evidence_edge_table.csv", edge_df)
    console.print(f"Wrote graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges.")


@app.command()
def query(
    target_outcome: str,
    current_mechanics: str = "",
    population: Optional[str] = None,
    context: Optional[str] = None,
    dataset_c: Path = Path("data/processed/mechanic_intervention_dataset.csv"),
) -> None:
    df = pd.read_csv(dataset_c) if dataset_c.exists() else pd.DataFrame()
    result = DesignQueryEngine(df).query(
        DesignQuery(
            target_outcome=target_outcome,
            current_mechanics=[x.strip() for x in current_mechanics.split(",") if x.strip()],
            population=population,
            context=context,
        )
    )
    console.print_json(data=result.model_dump(mode="json"))


@app.command()
def validate() -> None:
    errors: list[str] = []
    study_path = Path("data/processed/study_ontology.json")
    game_path = Path("data/processed/game_ontology.json")
    dataset_path = Path("data/processed/mechanic_intervention_dataset.csv")
    if study_path.exists():
        errors.extend(validate_study_ontology(StudyOntology.model_validate_json(study_path.read_text())))
    if game_path.exists():
        errors.extend(validate_game_ontology(GameOntology.model_validate_json(game_path.read_text())))
    if dataset_path.exists():
        errors.extend(validate_dataset_c(pd.read_csv(dataset_path)))
    if errors:
        for error in errors:
            console.print(f"[red]{error}[/red]")
        raise typer.Exit(1)
    console.print("Validation passed.")


@app.command()
def report(dataset_c: Path = Path("data/processed/mechanic_intervention_dataset.csv")) -> None:
    df = pd.read_csv(dataset_c) if dataset_c.exists() else pd.DataFrame()
    graph_path = Path("data/processed/causal_claim_graph.json")
    nodes = edges = 0
    if graph_path.exists():
        payload = json.loads(graph_path.read_text())
        nodes = len(payload.get("nodes", []))
        edges = len(payload.get("edges", []))
    write_csv(Path("data/processed/completeness_report.csv"), build_completeness_report(df, nodes, edges))
    write_audit_report(df, "data/processed/extraction_audit_report.md")
    console.print("Wrote completeness and audit reports.")


@app.command("run-all")
def run_all(pdf_dir: Path = Path("data/input/papers"), out: Path = Path("data/processed")) -> None:
    _ensure_project_dirs()
    docs = ingest_pdf_folder(pdf_dir, "data/intermediate")
    studies = asyncio.run(extract_study_ontology(get_llm_client(), docs))
    write_json(out / "study_ontology.json", studies)
    games = build_game_ontology(studies, "data/input/seed_game_ontology.json")
    write_json(out / "game_ontology.json", games)
    df = build_dataset_c(studies, games)
    write_csv(out / "mechanic_intervention_dataset.csv", df)
    write_jsonl(out / "mechanic_intervention_dataset.jsonl", df.to_dict(orient="records"))
    graph = build_evidence_graph(df) if not df.empty else build_evidence_graph(pd.DataFrame(columns=[]))
    write_json(out / "causal_claim_graph.json", graph)
    export_graphml(graph, out / "causal_claim_graph.graphml")
    write_csv(out / "evidence_edge_table.csv", pd.DataFrame([edge.model_dump(mode="json") for edge in graph.edges]))
    write_csv(out / "completeness_report.csv", build_completeness_report(df, len(graph.nodes), len(graph.edges)))
    write_audit_report(df, out / "extraction_audit_report.md")
    items = build_review_queue(df)
    write_review_jsonl(items, out / "review_queue.jsonl")
    write_json(out / "design_query_examples.json", {"examples": []})
    console.print(f"Processed {len(docs)} PDFs; wrote required outputs to {out}.")


@review_app.command("export")
def review_export(
    queue: Path = Path("data/processed/review_queue.jsonl"),
    output: Path = Path("data/review/review_queue.csv"),
) -> None:
    export_review_csv(queue, output)
    console.print(f"Exported review queue to {output}.")


@review_app.command("apply")
def review_apply(input: Path = Path("data/review/review_decisions.csv")) -> None:
    console.print(f"Review decision application scaffold read from {input}.")


@review_app.command("ui")
def review_ui() -> None:
    from game_evidence_graph.review.reviewer_ui import run_review_ui

    run_review_ui()


@recite_app.command("inspect")
def recite_inspect(repo_path: Path) -> None:
    console.print_json(data=inspect_repo(repo_path))


@recite_app.command("report")
def recite_report(repo_path: Path, out: Path = Path("docs/recite_adaptation_report.md")) -> None:
    write_adaptation_report(repo_path, out)
    console.print(f"Wrote ReCITE adaptation report to {out}.")


@eval_app.command("graph")
def eval_graph(gold: Path, pred: Path) -> None:
    gold_payload = json.loads(gold.read_text())
    pred_payload = json.loads(pred.read_text())
    metrics = graph_edge_metrics(gold_payload.get("edges", []), pred_payload.get("edges", []))
    console.print_json(data=metrics)


@eval_app.command("dataset-c")
def eval_dataset_c(gold: Path, pred: Path) -> None:
    gold_df = pd.read_csv(gold)
    pred_df = pd.read_csv(pred)
    console.print_json(data={"gold_rows": len(gold_df), "pred_rows": len(pred_df)})


if __name__ == "__main__":
    app()
