from __future__ import annotations

from game_evidence_graph.llm.base import LLMClient


class MockLLMClient(LLMClient):
    def __init__(self, responses: list[dict] | None = None):
        self.responses = list(responses or [])

    async def complete_json(self, prompt: str) -> dict:
        if self.responses:
            return self.responses.pop(0)
        return {}
