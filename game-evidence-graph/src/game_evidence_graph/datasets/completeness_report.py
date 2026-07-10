from __future__ import annotations

from pathlib import Path

import pandas as pd


def build_completeness_report(df: pd.DataFrame, graph_nodes: int = 0, graph_edges: int = 0) -> pd.DataFrame:
    total = max(len(df), 1)
    rows = [
        ("dataset_c_rows", len(df)),
        ("unique_papers", df["paper_id"].nunique() if "paper_id" in df else 0),
        ("unique_studies", df["study_id"].nunique() if "study_id" in df else 0),
        ("unique_interventions", df["intervention_id"].nunique() if "intervention_id" in df else 0),
        ("unique_conditions", df["condition_id"].nunique() if "condition_id" in df else 0),
        ("unique_games", df["game_id"].nunique() if "game_id" in df else 0),
        ("unique_mechanics", df["mechanic_id"].nunique() if "mechanic_id" in df else 0),
        ("unique_mechanic_sets", df["mechanic_set_id"].nunique() if "mechanic_set_id" in df else 0),
        ("unique_outcomes", df["outcome_id"].nunique() if "outcome_id" in df else 0),
        ("unique_measurements", df["measurement_id"].nunique() if "measurement_id" in df else 0),
        ("graph_nodes", graph_nodes),
        ("graph_edges", graph_edges),
        ("percent_with_source_quotes", round(100 * df["source_quote"].notna().sum() / total, 2) if "source_quote" in df else 0),
        ("percent_with_source_pages", round(100 * df["source_page"].notna().sum() / total, 2) if "source_page" in df else 0),
        ("percent_with_numeric_effect_sizes", round(100 * df["effect_size_numeric"].notna().sum() / total, 2) if "effect_size_numeric" in df else 0),
        ("percent_with_p_values", round(100 * df["p_value"].notna().sum() / total, 2) if "p_value" in df else 0),
        ("percent_needing_human_review", round(100 * (df["review_status"] == "needs_review").sum() / total, 2) if "review_status" in df else 0),
    ]
    return pd.DataFrame(rows, columns=["metric", "value"])


def write_audit_report(df: pd.DataFrame, out_path: str | Path) -> None:
    warnings: list[str] = []
    if len(df):
        blanks = df[df["effect_direction"].isin(["not_reported", "unclear"])]
        events = df[df["attribution_level"] == "event_level"]
        inferred = df[df["attribution_level"].isin(["ontology_inferred_mechanic", "mechanic_set_inferred"])]
        if len(blanks):
            warnings.append(f"{len(blanks)} rows have missing effect evidence and were excluded from graph weighting.")
        if len(events):
            warnings.append(f"{len(events)} rows were marked event_level and should be excluded from mechanic-level aggregation.")
        if len(inferred):
            warnings.append(f"{len(inferred)} rows are inferred and require cautious interpretation.")
    text = [
        "# Extraction Audit Report",
        "",
        "This report describes a literature-derived evidence graph, not a structural causal model.",
        "",
        "## Warnings",
        *(f"- {warning}" for warning in warnings),
    ]
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(text) + "\n")
