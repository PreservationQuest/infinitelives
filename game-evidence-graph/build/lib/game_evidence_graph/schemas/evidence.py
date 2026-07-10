from __future__ import annotations

from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class EvidenceStrength(StrEnum):
    randomized_controlled_trial = "randomized_controlled_trial"
    quasi_experimental = "quasi_experimental"
    case_control = "case_control"
    within_subject_experimental = "within_subject_experimental"
    within_subject_observational = "within_subject_observational"
    between_subject_observational = "between_subject_observational"
    correlational = "correlational"
    pre_post_no_control = "pre_post_no_control"
    qualitative = "qualitative"
    mixed_methods = "mixed_methods"
    not_reported = "not_reported"
    unclear = "unclear"


class EffectDirection(StrEnum):
    positive = "positive"
    negative = "negative"
    null = "null"
    mixed = "mixed"
    not_reported = "not_reported"
    unclear = "unclear"


class AttributionLevel(StrEnum):
    paper_explicit_mechanic = "paper_explicit_mechanic"
    paper_explicit_intervention = "paper_explicit_intervention"
    ontology_inferred_mechanic = "ontology_inferred_mechanic"
    mechanic_set_inferred = "mechanic_set_inferred"
    event_level = "event_level"
    unsupported_or_overgenerated = "unsupported_or_overgenerated"


class ClaimType(StrEnum):
    reported_causal_claim = "reported_causal_claim"
    reported_intervention_effect = "reported_intervention_effect"
    reported_association = "reported_association"
    mechanism_hypothesis = "mechanism_hypothesis"
    ontology_inferred_link = "ontology_inferred_link"
    unsupported_or_overgenerated = "unsupported_or_overgenerated"


class ClaimExplicitness(StrEnum):
    explicit = "explicit"
    implicit = "implicit"
    inferred = "inferred"
    absent_or_unsupported = "absent_or_unsupported"


class ReviewStatus(StrEnum):
    auto_extracted = "auto_extracted"
    needs_review = "needs_review"
    human_verified = "human_verified"
    pending = "pending"


class EvidenceTrace(BaseModel):
    paper_id: str
    study_id: Optional[str] = None
    intervention_id: Optional[str] = None
    condition_id: Optional[str] = None
    outcome_id: Optional[str] = None
    measurement_id: Optional[str] = None
    source_quote: Optional[str] = None
    source_page: Optional[int] = None
    page_trace_status: str = "found"
    evidence_strength: EvidenceStrength = EvidenceStrength.unclear
    attribution_level: AttributionLevel
    claim_type: ClaimType
    claim_explicitness: ClaimExplicitness
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    review_status: ReviewStatus = ReviewStatus.needs_review

    @field_validator("page_trace_status")
    @classmethod
    def source_page_or_status(cls, value: str, info):
        source_page = info.data.get("source_page")
        if source_page is None and value == "found":
            return "not_found"
        return value
