from game_evidence_graph.datasets.mechanic_intervention_builder import build_dataset_c
from game_evidence_graph.graph.evidence_graph_builder import build_evidence_graph
from tests.support import sample_study


def test_graph_builder_creates_evidence_edges():
    studies, games = sample_study(effect=True)
    graph = build_evidence_graph(build_dataset_c(studies, games))
    assert graph.nodes
    assert graph.edges
    assert all(edge.source_quote for edge in graph.edges)
    assert {edge.edge_type for edge in graph.edges} == {"MECHANIC_SET_ASSOCIATED_WITH_OUTCOME"}
