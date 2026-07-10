from __future__ import annotations

from game_evidence_graph.datasets.exporters import write_json
from game_evidence_graph.schemas.graph import EvidenceGraphPayload


def export_graph_json(graph: EvidenceGraphPayload, path: str) -> None:
    write_json(path, graph)
