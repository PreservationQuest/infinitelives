from __future__ import annotations


def has_reported_effect(outcome: dict) -> bool:
    return any(
        outcome.get(field)
        for field in ["effect_size_raw", "effect_size_numeric", "p_value", "confidence_interval"]
    ) or outcome.get("effect_direction") not in {None, "not_reported", "unclear"}
