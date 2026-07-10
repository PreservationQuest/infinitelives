from __future__ import annotations

from rapidfuzz import process

from game_evidence_graph.canonicalization.text_normalization import normalize_text


def match_outcome(name: str, vocabulary: list[str]) -> tuple[str, str, float]:
    if not vocabulary:
        return "unclear", "needs_review", 0.0
    normalized_vocab = {normalize_text(v): v for v in vocabulary}
    match = process.extractOne(normalize_text(name), list(normalized_vocab.keys()))
    if not match:
        return "unclear", "needs_review", 0.0
    value = normalized_vocab[match[0]]
    score = float(match[1])
    if score >= 90:
        return value, "high", score
    if score >= 75:
        return value, "medium", score
    return "unclear", "needs_review", score
