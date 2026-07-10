from __future__ import annotations

from game_evidence_graph.llm.base import LLMClient
from game_evidence_graph.llm.prompts import CAUSAL_CLAIM_EDGE_PROMPT


async def extract_causal_claim_edges(client: LLMClient, paper_text: str, context: dict) -> list[dict]:
    payload = await client.complete_json(
        f"{CAUSAL_CLAIM_EDGE_PROMPT}\nContext: {context}\nPaper text:\n{paper_text}"
    )
    return payload.get("causal_claim_edges", [])
