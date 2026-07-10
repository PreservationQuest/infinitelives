from __future__ import annotations

import pandas as pd

from game_evidence_graph.schemas.evidence import AttributionLevel, ClaimExplicitness, ClaimType
from game_evidence_graph.schemas.graph import EvidenceGraphPayload, GraphEdge, GraphNode


def _node(nodes: dict[str, GraphNode], node_id: str, node_type: str, label: str) -> None:
    if node_id and node_id not in nodes:
        nodes[node_id] = GraphNode(node_id=node_id, node_type=node_type, label=str(label or node_id))


def _value(row, key: str):
    value = row.get(key)
    return None if pd.isna(value) else value


def _text(row, key: str) -> str | None:
    value = _value(row, key)
    return None if value is None else str(value)


def build_evidence_graph(df: pd.DataFrame) -> EvidenceGraphPayload:
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []
    edge_idx = 1
    for _, row in df.iterrows():
        _node(nodes, row["paper_id"], "Paper", row.get("paper_title") or row["paper_id"])
        _node(nodes, row["study_id"], "Study", row["study_id"])
        _node(nodes, row["intervention_id"], "Intervention", row["intervention_id"])
        _node(nodes, row["condition_id"], "Condition", row["condition_id"])
        if pd.notna(row.get("game_id")):
            _node(nodes, row["game_id"], "Game", row.get("game_name"))
        if pd.notna(row.get("mechanic_set_id")):
            _node(nodes, row["mechanic_set_id"], "MechanicSet", row.get("co_mechanics") or row["mechanic_set_id"])
        if pd.notna(row.get("mechanic_id")):
            node_type = "GameEvent" if row["attribution_level"] == "event_level" else "Mechanic"
            _node(nodes, row["mechanic_id"], node_type, row.get("mechanic_name"))
        _node(nodes, row["outcome_id"], "Outcome", row.get("outcome_canonical") or row["outcome_raw"])
        _node(nodes, row["measurement_id"], "Measurement", row.get("measurement_type") or row["measurement_raw"])

        edge_type = "UNSUPPORTED_OR_OVERGENERATED"
        if bool(row.get("is_supported_evidence")):
            if row["attribution_level"] == "event_level":
                edge_type = "GAME_EVENT_ASSOCIATED_WITH_OUTCOME"
                source_id = row["mechanic_id"]
                source_type = "GameEvent"
            else:
                edge_type = "MECHANIC_SET_ASSOCIATED_WITH_OUTCOME"
                source_id = row["mechanic_set_id"]
                source_type = "MechanicSet"
            edges.append(
                GraphEdge(
                    edge_id=f"edge_{edge_idx:06d}",
                    source_node_id=source_id,
                    source_node_type=source_type,
                    target_node_id=row["outcome_id"],
                    target_node_type="Outcome",
                    edge_type=edge_type,
                    paper_id=_text(row, "paper_id"),
                    study_id=_text(row, "study_id"),
                    intervention_id=_text(row, "intervention_id"),
                    condition_id=_text(row, "condition_id"),
                    population_id=_text(row, "population_id"),
                    context=_text(row, "context"),
                    duration=_text(row, "duration"),
                    outcome_id=_text(row, "outcome_id"),
                    measurement_id=_text(row, "measurement_id"),
                    effect_direction=_text(row, "effect_direction"),
                    effect_size_raw=_text(row, "effect_size_raw"),
                    effect_size_numeric=_value(row, "effect_size_numeric"),
                    effect_metric=_text(row, "effect_metric"),
                    p_value=_text(row, "p_value"),
                    confidence_interval=_text(row, "confidence_interval"),
                    evidence_strength=_text(row, "evidence_strength") or "unclear",
                    attribution_level=AttributionLevel(row["attribution_level"]),
                    claim_type=ClaimType(row["claim_type"]),
                    claim_explicitness=ClaimExplicitness(row["claim_explicitness"]),
                    source_quote=_text(row, "source_quote"),
                    source_page=int(row["source_page"]) if pd.notna(row.get("source_page")) else None,
                    extraction_confidence=float(row.get("extraction_confidence") or 0),
                    review_status=row.get("review_status") or "needs_review",
                    edge_weight=float(row.get("edge_weight") or 0),
                )
            )
            edge_idx += 1
    return EvidenceGraphPayload(nodes=list(nodes.values()), edges=edges)
