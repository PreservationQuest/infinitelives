from game_evidence_graph.canonicalization.game_matcher import match_game
from game_evidence_graph.schemas.game import GameRecord


def test_game_exact_alias_match():
    result = match_game("Counter Strike", [GameRecord(game_id="g01", canonical_game_name="Counter-Strike", aliases=["Counter Strike"])])
    assert result.game_id == "g01"
    assert not result.needs_review
