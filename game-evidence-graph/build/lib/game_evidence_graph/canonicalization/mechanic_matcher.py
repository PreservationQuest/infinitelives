from __future__ import annotations

from rapidfuzz import fuzz

from game_evidence_graph.canonicalization.text_normalization import normalize_text
from game_evidence_graph.schemas.mechanic import MechanicDefinition


def match_mechanic(name: str, definitions: list[MechanicDefinition]) -> tuple[str | None, str, float]:
    normalized = normalize_text(name)
    best_id, best_score = None, 0.0
    for definition in definitions:
        for candidate in [definition.canonical_name, *definition.aliases]:
            score = fuzz.token_sort_ratio(normalized, normalize_text(candidate))
            if score > best_score:
                best_id, best_score = definition.mechanic_id, score
    if best_score >= 94:
        return best_id, "high", best_score
    if best_score >= 80:
        return best_id, "medium", best_score
    return None, "needs_review", best_score
