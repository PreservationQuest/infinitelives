import pytest

from game_evidence_graph.schemas.evidence import AttributionLevel, ClaimExplicitness, ClaimType
from game_evidence_graph.schemas.graph import GraphEdge


def test_evidence_edge_requires_source_quote():
    with pytest.raises(ValueError):
        GraphEdge(
            edge_id="edge_000001",
            source_node_id="ms_0001",
            source_node_type="MechanicSet",
            target_node_id="out_001",
            target_node_type="Outcome",
            edge_type="MECHANIC_SET_ASSOCIATED_WITH_OUTCOME",
            attribution_level=AttributionLevel.mechanic_set_inferred,
            claim_type=ClaimType.reported_intervention_effect,
            claim_explicitness=ClaimExplicitness.inferred,
        )
