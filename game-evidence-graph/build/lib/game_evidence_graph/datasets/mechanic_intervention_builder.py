from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from game_evidence_graph.graph.edge_weighting import support_score
from game_evidence_graph.schemas.game import GameOntology, GameRecord
from game_evidence_graph.schemas.study import Outcome, StudyOntology, StudyRecord

DATASET_C_COLUMNS = [
    "paper_id",
    "paper_title",
    "year",
    "doi",
    "study_id",
    "intervention_id",
    "condition_id",
    "condition_type",
    "game_id",
    "game_name",
    "game_match_confidence",
    "mechanic_id",
    "mechanic_name",
    "mechanic_match_confidence",
    "mechanic_set_id",
    "co_mechanics",
    "population_id",
    "population_raw",
    "sample_size",
    "age_range",
    "country",
    "context",
    "duration",
    "study_design",
    "treatment_raw",
    "control_raw",
    "outcome_id",
    "outcome_raw",
    "outcome_canonical",
    "outcome_category",
    "outcome_match_confidence",
    "measurement_id",
    "measurement_raw",
    "measurement_type",
    "measurement_match_confidence",
    "effect_direction",
    "effect_size_raw",
    "effect_size_numeric",
    "effect_metric",
    "p_value",
    "confidence_interval",
    "effect_target_measure",
    "evidence_strength",
    "attribution_level",
    "claim_type",
    "claim_explicitness",
    "source_quote",
    "source_page",
    "page_trace_status",
    "extraction_confidence",
    "is_supported_evidence",
    "edge_weight",
    "review_status",
    "notes",
]

EVENT_TERMS = {"slay event", "slain event", "win event", "loss event", "boss defeat", "death event"}


@dataclass
class MechanicContext:
    game: GameRecord | None
    mechanics: list[tuple[str | None, str]]

    @property
    def game_id(self) -> str | None:
        return self.game.game_id if self.game else None

    @property
    def game_name(self) -> str | None:
        return self.game.canonical_game_name if self.game else None

    @property
    def game_match_confidence(self) -> str:
        return self.game.game_match_confidence if self.game else "needs_review"


def _games_by_id(game_ontology: GameOntology) -> dict[str, GameRecord]:
    return {game.game_id: game for game in game_ontology.games}


def _mechanic_context(condition_game_ids: list[str], games: dict[str, GameRecord]) -> list[MechanicContext]:
    contexts: list[MechanicContext] = []
    for game_id in condition_game_ids:
        game = games.get(game_id)
        if not game:
            continue
        mechanics = [
            (feature.mechanic_id, feature.mechanic_name or "")
            for feature in game.mechanics
            if feature.mechanic_name
        ]
        contexts.append(MechanicContext(game=game, mechanics=mechanics or [(None, "not_reported")]))
    return contexts or [MechanicContext(game=None, mechanics=[(None, "not_reported")])]


def _is_blank_effect(outcome) -> bool:
    return (
        outcome.effect_direction in {"not_reported", "unclear"}
        and outcome.effect_size_raw is None
        and outcome.effect_size_numeric is None
        and outcome.p_value is None
    )


def _fallback_outcomes(study: StudyRecord) -> list[Outcome]:
    if study.outcomes:
        return study.outcomes
    return [
        Outcome(
            outcome_id=f"{study.study_id}_out_{idx:03d}",
            outcome_raw=condition,
            outcome_canonical="unclear",
            outcome_category="unclear",
            measurement_id=f"{study.study_id}_meas_{idx:03d}",
            measurement_raw=None,
            effect_direction="not_reported",
            source_quote=None,
            source_page=None,
            page_trace_status="not_found",
        )
        for idx, condition in enumerate(study.studied_conditions, start=1)
    ]


def _base_row(study: StudyRecord, intervention, condition, outcome, ctx: MechanicContext) -> dict[str, Any]:
    blank_effect = _is_blank_effect(outcome)
    has_reported_direction = outcome.effect_direction.value not in {"not_reported", "unclear"}
    extraction_confidence = study.extraction_confidence or 0.0
    unsupported = blank_effect or not has_reported_direction
    attribution_level = "unsupported_or_overgenerated" if unsupported else "mechanic_set_inferred"
    claim_type = "unsupported_or_overgenerated" if unsupported else "reported_intervention_effect"
    claim_explicitness = "absent_or_unsupported" if unsupported else "inferred"
    is_supported = not unsupported and bool(outcome.source_quote)
    edge_weight = (
        0.0
        if not is_supported
        else support_score(
            evidence_strength=str(study.evidence_strength.value),
            extraction_confidence=extraction_confidence,
            attribution_level=attribution_level,
            effect_size_numeric=outcome.effect_size_numeric,
            p_value=outcome.p_value,
            effect_direction=str(outcome.effect_direction.value),
        )
    )
    return {
        "paper_id": study.paper_id,
        "paper_title": study.paper_title,
        "year": study.year,
        "doi": study.doi,
        "study_id": study.study_id,
        "intervention_id": intervention.intervention_id,
        "condition_id": condition.condition_id,
        "condition_type": condition.condition_type,
        "game_id": ctx.game_id,
        "game_name": ctx.game_name,
        "game_match_confidence": ctx.game_match_confidence,
        "mechanic_set_id": f"ms_{abs(hash((study.study_id, intervention.intervention_id, condition.condition_id, ctx.game_id))) % 100000:05d}",
        "co_mechanics": "|".join(name for _, name in ctx.mechanics if name and name != "not_reported"),
        "population_id": study.population.population_id,
        "population_raw": study.population.population_raw,
        "sample_size": study.population.sample_size,
        "age_range": study.population.age_range,
        "country": study.population.country,
        "context": study.context,
        "duration": study.intervention_duration,
        "study_design": study.study_design.value,
        "treatment_raw": intervention.treatment_raw,
        "control_raw": intervention.control_raw,
        "outcome_id": outcome.outcome_id,
        "outcome_raw": outcome.outcome_raw,
        "outcome_canonical": outcome.outcome_canonical,
        "outcome_category": outcome.outcome_category,
        "outcome_match_confidence": "needs_review" if outcome.outcome_canonical == "unclear" else "high",
        "measurement_id": outcome.measurement_id,
        "measurement_raw": outcome.measurement_raw,
        "measurement_type": outcome.measurement_type,
        "measurement_match_confidence": "needs_review" if not outcome.measurement_type else "high",
        "effect_direction": outcome.effect_direction.value,
        "effect_size_raw": outcome.effect_size_raw,
        "effect_size_numeric": outcome.effect_size_numeric,
        "effect_metric": outcome.effect_metric,
        "p_value": outcome.p_value,
        "confidence_interval": outcome.confidence_interval,
        "effect_target_measure": outcome.effect_target_measure,
        "evidence_strength": study.evidence_strength.value,
        "attribution_level": attribution_level,
        "claim_type": claim_type,
        "claim_explicitness": claim_explicitness,
        "source_quote": outcome.source_quote,
        "source_page": outcome.source_page,
        "page_trace_status": outcome.page_trace_status,
        "extraction_confidence": extraction_confidence,
        "is_supported_evidence": is_supported,
        "edge_weight": edge_weight,
        "review_status": "needs_review" if unsupported or not outcome.source_quote else study.review_status.value,
        "notes": "Blank or unclear effect evidence; excluded from graph weighting." if unsupported else "",
    }


def build_mechanic_intervention_rows(
    study_ontology: StudyOntology, game_ontology: GameOntology
) -> list[dict[str, Any]]:
    games = _games_by_id(game_ontology)
    rows: list[dict[str, Any]] = []
    for study in study_ontology.studies:
        for intervention in study.interventions:
            for condition in intervention.conditions:
                for ctx in _mechanic_context(condition.game_ids, games):
                    for outcome in _fallback_outcomes(study):
                        row_base = _base_row(study, intervention, condition, outcome, ctx)
                        for mechanic_id, mechanic_name in ctx.mechanics:
                            row = dict(row_base)
                            mechanic_lower = (mechanic_name or "").lower()
                            if mechanic_lower in EVENT_TERMS:
                                row["attribution_level"] = "event_level"
                                row["notes"] = "In-game event, not a reusable game mechanic."
                            row["mechanic_id"] = mechanic_id
                            row["mechanic_name"] = mechanic_name
                            row["mechanic_match_confidence"] = "needs_review" if not mechanic_id else "high"
                            if row["attribution_level"] == "event_level":
                                row["edge_weight"] = support_score(
                                    row["evidence_strength"],
                                    row["extraction_confidence"],
                                    "event_level",
                                    row["effect_size_numeric"],
                                    row["p_value"],
                                    row["effect_direction"],
                                )
                            if row["attribution_level"] == "unsupported_or_overgenerated":
                                row["edge_weight"] = 0.0
                                row["is_supported_evidence"] = False
                            rows.append({col: row.get(col) for col in DATASET_C_COLUMNS})
    return rows


def build_dataset_c(study_ontology: StudyOntology, game_ontology: GameOntology) -> pd.DataFrame:
    return pd.DataFrame(build_mechanic_intervention_rows(study_ontology, game_ontology), columns=DATASET_C_COLUMNS)
