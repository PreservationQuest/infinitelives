from game_evidence_graph.datasets.mechanic_intervention_builder import build_dataset_c
from tests.support import sample_study


def test_every_mechanic_row_has_attribution_level():
    studies, games = sample_study(effect=True)
    df = build_dataset_c(studies, games)
    assert df["attribution_level"].notna().all()
