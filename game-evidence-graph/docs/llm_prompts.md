# LLM Prompts

Prompts live in `src/game_evidence_graph/llm/prompts.py`.

Core rules:

- Do not invent information.
- Return null, `not_reported`, `unclear`, or `needs_review` for missing information.
- Preserve exact source quotes and source pages when possible.
- Separate treatment from control.
- Separate measured outcomes from interpreted constructs.
- Separate game-level claims from mechanic-level claims.
- Separate mechanics from in-game events.
- Do not output chain-of-thought.
- Output strict JSON only.
