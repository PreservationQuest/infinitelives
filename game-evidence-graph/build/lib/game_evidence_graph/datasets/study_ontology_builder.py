from __future__ import annotations

import json
from pathlib import Path

from game_evidence_graph.schemas.study import StudyOntology, StudyRecord


def load_study_ontology(path: str | Path) -> StudyOntology:
    data = json.loads(Path(path).read_text())
    return StudyOntology.model_validate(data)


def build_study_ontology(records: list[dict]) -> StudyOntology:
    return StudyOntology(studies=[StudyRecord.model_validate(record) for record in records])
