from game_evidence_graph.canonicalization.outcome_matcher import match_outcome


def test_outcome_matching():
    value, confidence, _ = match_outcome("concept map performance", ["concept_map_performance", "empathy"])
    assert value == "concept_map_performance"
    assert confidence in {"high", "medium"}
