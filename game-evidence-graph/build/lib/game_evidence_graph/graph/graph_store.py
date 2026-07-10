from __future__ import annotations

from game_evidence_graph.graph.export_graphml import to_networkx
from game_evidence_graph.schemas.graph import EvidenceGraphPayload


class GraphStore:
    def __init__(self, payload: EvidenceGraphPayload):
        self.payload = payload
        self.graph = to_networkx(payload)

    def summary(self) -> dict:
        return {"nodes": self.graph.number_of_nodes(), "edges": self.graph.number_of_edges()}
