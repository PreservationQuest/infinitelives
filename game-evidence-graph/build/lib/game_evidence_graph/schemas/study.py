from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from game_evidence_graph.schemas.evidence import EffectDirection, EvidenceStrength, ReviewStatus


class Population(BaseModel):
    population_id: str
    population_raw: Optional[str] = None
    studied_conditions: list[str] = []
    age_range: Optional[str] = None
    mean_age: Optional[float] = None
    sample_size: Optional[int] = None
    gender: Optional[str] = None
    country: Optional[str] = None
    prior_gaming_experience: Optional[str] = None
    population_category: list[str] = []


class Condition(BaseModel):
    condition_id: str
    condition_type: str
    description: Optional[str] = None
    game_mentions: list[str] = []
    game_ids: list[str] = []


class Intervention(BaseModel):
    intervention_id: str
    intervention_name: Optional[str] = None
    treatment_raw: Optional[str] = None
    control_raw: Optional[str] = None
    conditions: list[Condition] = []


class Outcome(BaseModel):
    outcome_id: str
    outcome_raw: str
    outcome_canonical: str = "unclear"
    outcome_category: str = "unclear"
    measurement_id: str
    measurement_raw: Optional[str] = None
    measurement_type: Optional[str] = None
    effect_direction: EffectDirection = EffectDirection.not_reported
    effect_size_raw: Optional[str] = None
    effect_size_numeric: Optional[float] = None
    effect_metric: Optional[str] = None
    p_value: Optional[str] = None
    confidence_interval: Optional[str] = None
    effect_target_measure: Optional[str] = None
    evidence_statement: Optional[str] = None
    source_quote: Optional[str] = None
    source_page: Optional[int] = None
    page_trace_status: str = "not_found"


class StudyRecord(BaseModel):
    paper_id: str
    paper_title: Optional[str] = None
    doi: Optional[str] = None
    year: Optional[int] = None
    venue: Optional[str] = None
    study_id: str
    study_label: Optional[str] = None
    research_categories: list[str] = []
    studied_conditions: list[str] = []
    population: Population
    study_design: EvidenceStrength = EvidenceStrength.unclear
    evidence_strength: EvidenceStrength = EvidenceStrength.unclear
    context: Optional[str] = None
    intervention_duration: Optional[str] = None
    interventions: list[Intervention] = Field(default_factory=list)
    outcomes: list[Outcome] = Field(default_factory=list)
    source_pdf: Optional[str] = None
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    review_status: ReviewStatus = ReviewStatus.needs_review


class StudyOntology(BaseModel):
    papers: list[dict] = []
    studies: list[StudyRecord] = []
