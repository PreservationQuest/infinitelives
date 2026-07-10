from __future__ import annotations

from pathlib import Path

import networkx as nx

from game_evidence_graph.schemas.graph import EvidenceGraphPayload


def to_networkx(payload: EvidenceGraphPayload) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    for node in payload.nodes:
        graph.add_node(node.node_id, node_type=node.node_type, label=node.label, **node.properties)
    for edge in payload.edges:
        attrs = edge.model_dump(mode="json")
        source = attrs.pop("source_node_id")
        target = attrs.pop("target_node_id")
        attrs = {k: ("" if v is None else v) for k, v in attrs.items()}
        graph.add_edge(source, target, key=edge.edge_id, **attrs)
    return graph


def export_graphml(payload: EvidenceGraphPayload, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(to_networkx(payload), p)
