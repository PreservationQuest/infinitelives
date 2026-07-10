from game_evidence_graph.datasets.mechanic_intervention_builder import build_dataset_c
from game_evidence_graph.query.design_query_engine import DesignQueryEngine
from game_evidence_graph.schemas.query import DesignQuery
from tests.support import sample_study


def test_query_requires_supporting_evidence():
    studies, games = sample_study(effect=False)
    result = DesignQueryEngine(build_dataset_c(studies, games)).query(DesignQuery(target_outcome="concept_map_performance"))
    assert not result.recommendations
    assert result.message == "No sufficiently supported recommendation found."


def test_query_returns_supported_recommendation():
    studies, games = sample_study(effect=True)
    result = DesignQueryEngine(build_dataset_c(studies, games)).query(DesignQuery(target_outcome="concept_map_performance"))
    assert result.recommendations
    assert result.recommendations[0].supporting_studies
