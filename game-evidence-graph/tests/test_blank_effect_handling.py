from game_evidence_graph.datasets.mechanic_intervention_builder import build_dataset_c
from tests.support import sample_study


def test_blank_effect_rows_not_supported():
    studies, games = sample_study(effect=False)
    df = build_dataset_c(studies, games)
    assert set(df["attribution_level"]) == {"unsupported_or_overgenerated"}
    assert not df["is_supported_evidence"].any()
    assert (df["edge_weight"] == 0).all()
    assert set(df["review_status"]) == {"needs_review"}
