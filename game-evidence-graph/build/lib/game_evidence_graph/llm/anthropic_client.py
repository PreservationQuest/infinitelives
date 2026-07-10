from __future__ import annotations

from game_evidence_graph.llm.base import LLMClient


class AnthropicClient(LLMClient):
    async def complete_json(self, prompt: str) -> dict:
        raise NotImplementedError("Anthropic client is a placeholder; use MockLLMClient in tests.")
