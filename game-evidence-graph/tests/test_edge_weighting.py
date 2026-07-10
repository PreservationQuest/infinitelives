from game_evidence_graph.graph.edge_weighting import support_score


def test_support_score_is_zero_for_unsupported():
    assert support_score("quasi_experimental", 0.9, "unsupported_or_overgenerated", p_value="p < .05") == 0


def test_support_score_positive_for_supported_bundle():
    assert support_score("quasi_experimental", 0.9, "mechanic_set_inferred", p_value="p < .05") > 0
