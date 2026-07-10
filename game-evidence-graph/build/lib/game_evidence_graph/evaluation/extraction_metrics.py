from __future__ import annotations

from game_evidence_graph.evaluation.graph_metrics import precision_recall_f1


def field_set(records: list[dict], key: str) -> set:
    return {record.get(key) for record in records if record.get(key) is not None}


def field_precision_recall(gold_records: list[dict], pred_records: list[dict], key: str) -> dict[str, float]:
    return precision_recall_f1(field_set(gold_records, key), field_set(pred_records, key))
