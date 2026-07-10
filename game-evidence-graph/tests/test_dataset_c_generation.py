from game_evidence_graph.datasets.mechanic_intervention_builder import build_dataset_c
from tests.support import sample_study


def test_dataset_c_has_required_traceability():
    studies, games = sample_study(effect=True)
    df = build_dataset_c(studies, games)
    assert len(df) == 2
    assert set(df["attribution_level"]) == {"mechanic_set_inferred"}
    assert df["source_quote"].notna().all()
    assert df["is_supported_evidence"].all()
    assert (df["edge_weight"] > 0).all()
