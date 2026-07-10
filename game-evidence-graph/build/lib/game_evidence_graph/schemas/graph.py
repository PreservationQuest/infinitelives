from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator

from game_evidence_graph.schemas.evidence import AttributionLevel, ClaimExplicitness, ClaimType


EVIDENCE_EDGE_TYPES = {
    "INTERVENTION_REPORTED_EFFECT_ON_OUTCOME",
    "MECHANIC_SET_ASSOCIATED_WITH_OUTCOME",
    "MECHANIC_ASSOCIATED_WITH_OUTCOME",
    "GAME_EVENT_ASSOCIATED_WITH_OUTCOME",
}


class GraphNode(BaseModel):
    node_id: str
    node_type: str
    label: str
    properties: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    edge_id: str
    source_node_id: str
    source_node_type: str
    target_node_id: str
    target_node_type: str
    edge_type: str
    paper_id: Optional[str] = None
    study_id: Optional[str] = None
    intervention_id: Optional[str] = None
    condition_id: Optional[str] = None
    population_id: Optional[str] = None
    context: Optional[str] = None
    duration: Optional[str] = None
    outcome_id: Optional[str] = None
    measurement_id: Optional[str] = None
    effect_direction: Optional[str] = None
    effect_size_raw: Optional[str] = None
    effect_size_numeric: Optional[float] = None
    effect_metric: Optional[str] = None
    p_value: Optional[str] = None
    confidence_interval: Optional[str] = None
    evidence_strength: str = "unclear"
    attribution_level: AttributionLevel
    claim_type: ClaimType
    claim_explicitness: ClaimExplicitness
    source_quote: Optional[str] = None
    source_page: Optional[int] = None
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    review_status: str = "needs_review"
    edge_weight: float = 0.0

    @model_validator(mode="after")
    def evidence_edges_need_traceability(self):
        if self.edge_type in EVIDENCE_EDGE_TYPES and not self.source_quote:
            raise ValueError("Evidence-bearing graph edges require source_quote.")
        if self.attribution_level == AttributionLevel.unsupported_or_overgenerated:
            self.edge_weight = 0.0
        return self


class EvidenceGraphPayload(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
