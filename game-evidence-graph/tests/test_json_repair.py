from game_evidence_graph.llm.json_repair import repair_json


def test_json_repair_extracts_fenced_json():
    result = repair_json('Here:\n```json\n{"relationships": [{"source": "a", "sink": "b",}]}\n```')
    assert result.repair_attempted
    assert result.repair_success
    assert result.validated_json["relationships"][0]["source"] == "a"
