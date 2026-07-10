from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from game_evidence_graph.canonicalization.text_normalization import normalize_text
from game_evidence_graph.schemas.game import GameRecord


@dataclass
class GameMatch:
    game_id: str | None
    confidence: str
    score: float
    needs_review: bool
    reason: str


def match_game(name: str, games: list[GameRecord]) -> GameMatch:
    normalized = normalize_text(name)
    for game in games:
        candidates = [game.canonical_game_name, *game.aliases]
        if normalized in {normalize_text(candidate) for candidate in candidates}:
            return GameMatch(game.game_id, "high", 100.0, False, "Exact normalized match.")

    best: tuple[GameRecord, float] | None = None
    for game in games:
        candidates = [game.canonical_game_name, *game.aliases]
        score = max(fuzz.token_sort_ratio(normalized, normalize_text(candidate)) for candidate in candidates)
        if best is None or score > best[1]:
            best = (game, score)
    if not best:
        return GameMatch(None, "needs_review", 0.0, False, "No existing games.")
    game, score = best
    if score >= 94:
        return GameMatch(game.game_id, "high", score, False, "High fuzzy match.")
    if score >= 75:
        return GameMatch(game.game_id, "medium", score, True, f"Fuzzy game match score {score:.0f}.")
    return GameMatch(None, "needs_review", score, False, f"Best fuzzy score {score:.0f} below threshold.")
