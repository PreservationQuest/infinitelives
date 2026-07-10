from __future__ import annotations

from pathlib import Path

import yaml


def effect_availability(effect_size_numeric, p_value, effect_direction: str | None) -> str:
    if effect_size_numeric is not None:
        return "numeric_effect_size_available"
    if p_value:
        return "p_value_only"
    if effect_direction and effect_direction not in {"not_reported", "unclear"}:
        return "qualitative_direction_only"
    return "no_effect_reported"


def load_weights(path: str | Path = "configs/evidence_weights.yaml") -> dict:
    p = Path(path)
    if not p.exists():
        p = Path(__file__).resolve().parents[3] / "configs/evidence_weights.yaml"
    return yaml.safe_load(p.read_text())


def support_score(
    evidence_strength: str,
    extraction_confidence: float,
    attribution_level: str,
    effect_size_numeric=None,
    p_value=None,
    effect_direction: str | None = None,
    weights: dict | None = None,
) -> float:
    weights = weights or load_weights()
    availability = effect_availability(effect_size_numeric, p_value, effect_direction)
    score = (
        weights["evidence_strength_weight"].get(evidence_strength, 0.10)
        * max(0.0, min(1.0, extraction_confidence or 0.0))
        * weights["attribution_level_weight"].get(attribution_level, 0.0)
        * weights["effect_availability_weight"].get(availability, 0.0)
    )
    return round(float(score), 4)
