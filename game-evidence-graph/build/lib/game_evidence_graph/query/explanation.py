from __future__ import annotations

import pandas as pd


def effect_summary(rows: pd.DataFrame) -> str:
    positives = (rows["effect_direction"] == "positive").sum()
    negatives = (rows["effect_direction"] == "negative").sum()
    mixed = (rows["effect_direction"] == "mixed").sum()
    return f"Positive evidence in {positives} rows; negative in {negatives}; mixed in {mixed}; no pooled effect estimated."


def caveats(rows: pd.DataFrame) -> list[str]:
    notes = []
    if rows["attribution_level"].isin(["mechanic_set_inferred", "ontology_inferred_mechanic"]).any():
        notes.append("Mechanics were studied as part of a bundle or inferred from ontology, not isolated individually.")
    if rows["effect_size_numeric"].isna().all():
        notes.append("Effect sizes were not consistently reported.")
    return notes
