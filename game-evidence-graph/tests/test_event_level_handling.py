from game_evidence_graph.datasets.mechanic_intervention_builder import build_dataset_c
from tests.support import sample_study


def test_event_level_not_treated_as_standard_mechanic():
    studies, games = sample_study(effect=True, mechanic_name="Slay event")
    df = build_dataset_c(studies, games)
    event = df[df["mechanic_name"] == "Slay event"].iloc[0]
    assert event["attribution_level"] == "event_level"
