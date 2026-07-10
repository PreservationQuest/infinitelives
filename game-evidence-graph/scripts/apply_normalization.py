from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from game_evidence_graph.datasets.completeness_report import (  # noqa: E402
    build_completeness_report,
    write_audit_report,
)
from game_evidence_graph.datasets.exporters import write_csv, write_json, write_jsonl  # noqa: E402
from game_evidence_graph.graph.evidence_graph_builder import build_evidence_graph  # noqa: E402
from game_evidence_graph.graph.export_graphml import export_graphml  # noqa: E402
from game_evidence_graph.review.review_queue import build_review_queue, write_review_jsonl  # noqa: E402
from game_evidence_graph.schemas.game import GameOntology  # noqa: E402
from game_evidence_graph.schemas.study import StudyOntology  # noqa: E402


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text()) if path.exists() else {}


def read_yaml_map(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text())
    return data if isinstance(data, dict) else {}


def normalize_value(value: object, mapping: dict[str, Any]) -> object:
    if pd.isna(value):
        return value
    text = str(value).strip()
    if text in mapping:
        return mapping[text]
    lowered = text.lower()
    for key, mapped in mapping.items():
        if str(key).strip().lower() == lowered:
            return mapped
    return value


def apply_column_map(df: pd.DataFrame, column: str, mapping: dict[str, Any]) -> int:
    if not mapping or column not in df.columns:
        return 0
    before = df[column].copy()
    df[column] = df[column].map(lambda value: normalize_value(value, mapping))
    return int((before.astype(str) != df[column].astype(str)).sum())


def update_study_titles(study_payload: dict[str, Any], title_overrides: dict[str, str]) -> int:
    if not title_overrides:
        return 0
    count = 0
    for paper in study_payload.get("papers", []):
        paper_id = paper.get("paper_id")
        if paper_id in title_overrides:
            paper["title"] = title_overrides[paper_id]
            count += 1
    for study in study_payload.get("studies", []):
        paper_id = study.get("paper_id")
        if paper_id in title_overrides:
            study["paper_title"] = title_overrides[paper_id]
            count += 1
    return count


def update_study_outcome_categories(study_payload: dict[str, Any], category_map: dict[str, Any]) -> int:
    if not category_map:
        return 0
    count = 0
    for study in study_payload.get("studies", []):
        for outcome in study.get("outcomes", []):
            old = outcome.get("outcome_category")
            new = normalize_value(old, category_map)
            if old != new:
                outcome["outcome_category"] = new
                count += 1
    return count


def update_game_ontology(
    game_payload: dict[str, Any],
    game_map: dict[str, Any],
    mechanic_map: dict[str, Any],
) -> dict[str, int]:
    counts = {"game_names": 0, "mechanics": 0}
    for game in game_payload.get("games", []):
        for field in ["game_name", "canonical_game_name"]:
            old = game.get(field)
            new = normalize_value(old, game_map)
            if old != new:
                game[field] = new
                counts["game_names"] += 1
        for feature_group in ["mechanics", "dynamics", "aesthetics"]:
            for feature in game.get(feature_group, []) or []:
                if "mechanic_name" in feature:
                    old = feature.get("mechanic_name")
                    new = normalize_value(old, mechanic_map)
                    if old != new:
                        feature["mechanic_name"] = new
                        counts["mechanics"] += 1
    return counts


def parse_row_index(item_id: object) -> int | None:
    text = str(item_id).strip()
    for prefix in ["row_", "row:"]:
        if text.startswith(prefix):
            text = text[len(prefix) :]
    try:
        return int(text)
    except ValueError:
        return None


def apply_audit_decisions(
    df: pd.DataFrame,
    study_payload: dict[str, Any],
    decisions_path: Path,
) -> dict[str, int]:
    counts = {"rows": 0, "titles": 0, "global_replacements": 0}
    if not decisions_path.exists() or decisions_path.stat().st_size == 0:
        return counts
    decisions = pd.read_csv(decisions_path).fillna("")
    if decisions.empty:
        return counts

    active = decisions[decisions["decision"].astype(str).str.strip().ne("")]
    for _, decision in active.iterrows():
        item_type = str(decision.get("item_type", "")).strip()
        item_id = str(decision.get("item_id", "")).strip()
        field = str(decision.get("field", "")).strip()
        action = str(decision.get("decision", "")).strip()
        old_value = decision.get("old_value", "")
        new_value = decision.get("new_value", "")

        if not field:
            continue
        if action == "set_null":
            new_value = pd.NA
        elif action not in {"edit", "canonicalize", "set_null"}:
            continue

        if item_type == "title" and field == "paper_title":
            paper_id = item_id
            df.loc[df["paper_id"].eq(paper_id), "paper_title"] = new_value
            update_study_titles(study_payload, {paper_id: new_value})
            counts["titles"] += 1
        elif item_type == "row":
            row_index = parse_row_index(item_id)
            if row_index is not None and row_index in df.index and field in df.columns:
                df.at[row_index, field] = new_value
                counts["rows"] += 1
        elif field in df.columns and old_value != "":
            mask = df[field].astype(str).eq(str(old_value))
            df.loc[mask, field] = new_value
            counts["global_replacements"] += int(mask.sum())
    return counts


def write_normalization_report(path: Path, counts: dict[str, Any]) -> None:
    lines = [
        "# Normalization Report",
        "",
        "This folder is a derived, non-destructive normalization layer built from `data/processed`.",
        "",
        "## Applied Changes",
    ]
    for key, value in counts.items():
        lines.append(f"- {key}: {value}")
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply conservative normalization maps and audit decisions to processed outputs."
    )
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    parser.add_argument("--configs", type=Path, default=Path("configs/normalization"))
    parser.add_argument("--audit", type=Path, default=Path("data/audit"))
    parser.add_argument("--out", type=Path, default=Path("data/normalized"))
    args = parser.parse_args()

    processed = args.processed
    configs = args.configs
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    category_map = read_yaml_map(configs / "outcome_category_map.yaml")
    game_map = read_yaml_map(configs / "game_name_map.yaml")
    mechanic_map = read_yaml_map(configs / "mechanic_name_map.yaml")
    title_overrides = read_yaml_map(configs / "title_overrides.yaml")

    df = pd.read_csv(processed / "mechanic_intervention_dataset.csv")
    study_payload = read_json(processed / "study_ontology.json")
    game_payload = read_json(processed / "game_ontology.json")

    counts: dict[str, Any] = {}
    if title_overrides:
        df["paper_title"] = df.apply(
            lambda row: title_overrides.get(row["paper_id"], row["paper_title"]),
            axis=1,
        )
    counts["dataset_outcome_category_mapped"] = apply_column_map(
        df, "outcome_category", category_map
    )
    counts["dataset_game_name_mapped"] = apply_column_map(df, "game_name", game_map)
    counts["dataset_mechanic_name_mapped"] = apply_column_map(
        df, "mechanic_name", mechanic_map
    )
    counts["title_overrides_applied"] = update_study_titles(study_payload, title_overrides)
    counts["study_outcome_categories_mapped"] = update_study_outcome_categories(
        study_payload, category_map
    )
    counts.update(
        {
            f"game_ontology_{key}_mapped": value
            for key, value in update_game_ontology(game_payload, game_map, mechanic_map).items()
        }
    )
    counts["audit_decisions"] = apply_audit_decisions(
        df, study_payload, args.audit / "audit_decisions.csv"
    )

    studies = StudyOntology.model_validate(study_payload)
    games = GameOntology.model_validate(game_payload)

    write_json(out / "study_ontology.json", studies)
    write_json(out / "game_ontology.json", games)
    write_csv(out / "mechanic_intervention_dataset.csv", df)
    write_jsonl(
        out / "mechanic_intervention_dataset.jsonl",
        df.where(pd.notna(df), None).to_dict(orient="records"),
    )

    graph = build_evidence_graph(df) if not df.empty else build_evidence_graph(pd.DataFrame())
    write_json(out / "causal_claim_graph.json", graph)
    export_graphml(graph, out / "causal_claim_graph.graphml")
    write_csv(out / "evidence_edge_table.csv", pd.DataFrame([edge.model_dump(mode="json") for edge in graph.edges]))
    write_csv(out / "completeness_report.csv", build_completeness_report(df, len(graph.nodes), len(graph.edges)))
    write_audit_report(df, out / "extraction_audit_report.md")
    write_review_jsonl(build_review_queue(df), out / "review_queue.jsonl")
    (out / "design_query_examples.json").write_text(json.dumps({"examples": []}, indent=2) + "\n")
    write_normalization_report(out / "normalization_report.md", counts)

    print(json.dumps(counts, indent=2, default=str))
    print(f"Wrote normalized outputs to {out}")


if __name__ == "__main__":
    main()
