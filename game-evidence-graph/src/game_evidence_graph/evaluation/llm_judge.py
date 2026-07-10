from __future__ import annotations

from game_evidence_graph.llm.base import LLMClient
from game_evidence_graph.evaluation.judge_prompts import judge_prompt


async def judge_dimension(client: LLMClient, dimension: str, gold: str, prediction: str) -> dict:
    return await client.complete_json(judge_prompt(dimension, gold, prediction))
