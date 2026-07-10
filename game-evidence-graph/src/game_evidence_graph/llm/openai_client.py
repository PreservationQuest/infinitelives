from __future__ import annotations

from typing import Optional

from game_evidence_graph.llm.base import LLMClient


class OpenAIClient(LLMClient):
    def __init__(self, model: str = "gpt-5-mini", api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key

    async def complete_json(self, prompt: str) -> dict:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise RuntimeError("Install openai to use OpenAIClient.") from exc
        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.responses.create(model=self.model, input=prompt)
        from game_evidence_graph.llm.json_repair import repair_json

        return repair_json(response.output_text).validated_json or {}
