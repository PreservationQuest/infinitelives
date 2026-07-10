from __future__ import annotations

from game_evidence_graph.datasets.game_ontology_builder import build_game_ontology
from game_evidence_graph.schemas.game import GameOntology
from game_evidence_graph.schemas.study import StudyOntology


def extract_game_ontology(studies: StudyOntology, seed_path: str | None = None) -> GameOntology:
    return build_game_ontology(studies, seed_path)
