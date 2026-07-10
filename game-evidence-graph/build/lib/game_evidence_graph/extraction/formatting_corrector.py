from __future__ import annotations

from typing import Any

from game_evidence_graph.llm.json_repair import JSONRepairResult, repair_json


def correct_formatting(raw_response: str, empty_structure: Any | None = None) -> JSONRepairResult:
    return repair_json(raw_response, empty_structure=empty_structure or {})
