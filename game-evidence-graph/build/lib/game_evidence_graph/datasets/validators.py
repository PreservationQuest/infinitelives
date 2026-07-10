from __future__ import annotations

import pandas as pd

from game_evidence_graph.datasets.mechanic_intervention_builder import DATASET_C_COLUMNS
from game_evidence_graph.schemas.game import GameOntology
from game_evidence_graph.schemas.study import StudyOntology


def validate_study_ontology(ontology: StudyOntology) -> list[str]:
    errors: list[str] = []
    for study in ontology.studies:
        if not study.interventions:
            errors.append(f"{study.study_id}: missing interventions")
        if not study.outcomes:
            errors.append(f"{study.study_id}: missing outcomes")
        if study.evidence_strength.value not in {item.value for item in type(study.evidence_strength)}:
            errors.append(f"{study.study_id}: invalid evidence_strength")
        for outcome in study.outcomes:
            if outcome.source_quote and outcome.source_page is None and outcome.page_trace_status == "found":
                errors.append(f"{study.study_id}/{outcome.outcome_id}: source_page missing status")
    return errors


def validate_game_ontology(ontology: GameOntology) -> list[str]:
    errors: list[str] = []
    names: set[str] = set()
    for game in ontology.games:
        if not game.game_id:
            errors.append("game missing game_id")
        if not game.canonical_game_name:
            errors.append(f"{game.game_id}: missing canonical_game_name")
        norm = game.canonical_game_name.lower()
        if norm in names:
            errors.append(f"{game.game_id}: duplicate game name")
        names.add(norm)
    return errors


def validate_dataset_c(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    missing = [col for col in DATASET_C_COLUMNS if col not in df.columns]
    if missing:
        errors.append(f"missing Dataset C columns: {missing}")
        return errors
    for idx, row in df.iterrows():
        prefix = f"row {idx}"
        if not row["attribution_level"]:
            errors.append(f"{prefix}: missing attribution_level")
        if row["is_supported_evidence"] and not row["source_quote"]:
            errors.append(f"{prefix}: supported evidence missing source_quote")
        if row["effect_direction"] == "not_reported" and bool(row["is_supported_evidence"]):
            errors.append(f"{prefix}: blank effect row marked supported")
        if row["attribution_level"] == "unsupported_or_overgenerated" and float(row["edge_weight"] or 0) != 0:
            errors.append(f"{prefix}: unsupported row has nonzero edge_weight")
        if "event" in str(row["mechanic_name"]).lower() and row["attribution_level"] != "event_level":
            errors.append(f"{prefix}: event-level row not marked event_level")
    return errors
