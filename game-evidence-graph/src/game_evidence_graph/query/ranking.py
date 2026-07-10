from __future__ import annotations

import pandas as pd


def rank_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    grouped = (
        df.groupby(["mechanic_set_id", "co_mechanics"], dropna=False)
        .agg(
            support_score=("edge_weight", "sum"),
            evidence_count=("study_id", "nunique"),
            best_evidence_strength=("evidence_strength", "first"),
        )
        .reset_index()
    )
    grouped["support_score"] = grouped["support_score"] + grouped["evidence_count"] * 0.02
    return grouped.sort_values(["support_score", "evidence_count"], ascending=False)
