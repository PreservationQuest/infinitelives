from __future__ import annotations

import pandas as pd

from game_evidence_graph.query.explanation import caveats, effect_summary
from game_evidence_graph.query.ranking import rank_rows
from game_evidence_graph.schemas.query import DesignQuery, DesignQueryResult, Recommendation, SupportingStudy


def _truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"true", "1", "yes"}


class DesignQueryEngine:
    def __init__(self, dataset_c: pd.DataFrame):
        self.dataset_c = dataset_c.copy()

    def query(self, query: DesignQuery) -> DesignQueryResult:
        df = self.dataset_c
        if df.empty:
            return DesignQueryResult(query=query, recommendations=[], message="No sufficiently supported recommendation found.")
        filtered = df[
            df["outcome_canonical"].fillna("").str.contains(query.target_outcome, case=False, regex=False)
            | df["outcome_raw"].fillna("").str.contains(query.target_outcome, case=False, regex=False)
        ].copy()
        filtered = filtered[filtered["is_supported_evidence"].map(_truthy)]
        if query.population:
            population_matches = filtered["population_raw"].fillna("").str.contains(query.population, case=False, regex=False)
            filtered = filtered[population_matches | filtered["population_raw"].isna()]
        if query.context:
            context_matches = filtered["context"].fillna("").str.contains(query.context, case=False, regex=False)
            filtered = filtered[context_matches | filtered["context"].isna()]
        if not query.include_inferred_edges:
            filtered = filtered[~filtered["attribution_level"].isin(["mechanic_set_inferred", "ontology_inferred_mechanic"])]
        for excluded in query.exclude_mechanics:
            filtered = filtered[~filtered["co_mechanics"].fillna("").str.contains(excluded, case=False, regex=False)]
        if filtered.empty:
            return DesignQueryResult(query=query, recommendations=[], message="No sufficiently supported recommendation found.")

        ranked = rank_rows(filtered).head(query.max_results)
        recommendations: list[Recommendation] = []
        for _, rank in ranked.iterrows():
            rows = filtered[filtered["mechanic_set_id"] == rank["mechanic_set_id"]]
            studies = [
                SupportingStudy(
                    paper_id=row["paper_id"],
                    study_id=row["study_id"],
                    population=row.get("population_raw"),
                    context=row.get("context"),
                    effect_direction=row.get("effect_direction"),
                    effect_size_raw=row.get("effect_size_raw"),
                    source_quote=row["source_quote"],
                    source_page=int(row["source_page"]) if pd.notna(row.get("source_page")) else None,
                )
                for _, row in rows.drop_duplicates(["paper_id", "study_id", "source_quote"]).iterrows()
            ]
            recommendations.append(
                Recommendation(
                    mechanic_or_set=[x for x in str(rank["co_mechanics"]).split("|") if x],
                    recommendation_type="mechanic_set",
                    target_outcome=query.target_outcome,
                    support_score=round(float(rank["support_score"]), 4),
                    effect_summary=effect_summary(rows),
                    evidence_count=int(rank["evidence_count"]),
                    best_evidence_strength=str(rank["best_evidence_strength"]),
                    attribution_levels=sorted(set(rows["attribution_level"].dropna())),
                    supporting_studies=studies,
                    caveats=caveats(rows),
                )
            )
        return DesignQueryResult(query=query, recommendations=recommendations)
