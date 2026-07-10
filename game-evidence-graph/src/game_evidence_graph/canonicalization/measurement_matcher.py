from __future__ import annotations

from game_evidence_graph.canonicalization.outcome_matcher import match_outcome


def match_measurement(name: str, vocabulary: list[str]) -> tuple[str, str, float]:
    return match_outcome(name, vocabulary)
