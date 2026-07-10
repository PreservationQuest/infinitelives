from game_evidence_graph.canonicalization.mechanic_matcher import match_mechanic
from game_evidence_graph.schemas.mechanic import MechanicDefinition


def test_mechanic_match_alias():
    mechanic_id, confidence, _ = match_mechanic(
        "physics manipulation",
        [MechanicDefinition(mechanic_id="m014", canonical_name="Physics Interaction", aliases=["physics manipulation"])],
    )
    assert mechanic_id == "m014"
    assert confidence == "high"
