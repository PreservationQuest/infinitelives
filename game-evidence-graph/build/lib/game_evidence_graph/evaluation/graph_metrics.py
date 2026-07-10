from __future__ import annotations


def precision_recall_f1(gold: set[tuple], pred: set[tuple]) -> dict[str, float]:
    tp = len(gold & pred)
    precision = tp / len(pred) if pred else 0.0
    recall = tp / len(gold) if gold else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def edge_tuple(edge: dict) -> tuple:
    return (edge.get("source_node_id"), edge.get("target_node_id"), edge.get("edge_type"))


def graph_edge_metrics(gold_edges: list[dict], pred_edges: list[dict]) -> dict[str, float]:
    return precision_recall_f1({edge_tuple(e) for e in gold_edges}, {edge_tuple(e) for e in pred_edges})


def structural_hamming_distance(gold_edges: list[dict], pred_edges: list[dict]) -> int:
    gold = {edge_tuple(e) for e in gold_edges}
    pred = {edge_tuple(e) for e in pred_edges}
    return len(gold - pred) + len(pred - gold)
