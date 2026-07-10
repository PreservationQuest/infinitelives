from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    async def complete_json(self, prompt: str) -> dict:
        """Return parsed JSON from a prompt."""
