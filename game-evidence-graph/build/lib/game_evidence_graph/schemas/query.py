from __future__ import annotations

from pydantic import BaseModel


class DesignQuery(BaseModel):
    target_outcome: str
    current_mechanics: list[str] = []
    population: str | None = None
    context: str | None = None
    exclude_mechanics: list[str] = []
    min_evidence_strength: str = "unclear"
    include_inferred_edges: bool = True
    max_results: int = 10


class SupportingStudy(BaseModel):
    paper_id: str
    study_id: str
    population: str | None = None
    context: str | None = None
    effect_direction: str | None = None
    effect_size_raw: str | None = None
    source_quote: str
    source_page: int | None = None


class Recommendation(BaseModel):
    mechanic_or_set: list[str]
    recommendation_type: str
    target_outcome: str
    support_score: float
    effect_summary: str
    evidence_count: int
    best_evidence_strength: str
    attribution_levels: list[str]
    supporting_studies: list[SupportingStudy]
    caveats: list[str] = []


class DesignQueryResult(BaseModel):
    query: DesignQuery
    recommendations: list[Recommendation]
    message: str | None = None
