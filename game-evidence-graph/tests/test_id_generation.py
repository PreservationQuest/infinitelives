from game_evidence_graph.canonicalization.ids import next_game_id, next_mechanic_id, sequential_id


def test_id_generation():
    assert sequential_id("edge_", 7, 6) == "edge_000007"
    assert next_game_id(["g01", "g02"]) == "g03"
    assert next_mechanic_id(["m001"]) == "m002"
