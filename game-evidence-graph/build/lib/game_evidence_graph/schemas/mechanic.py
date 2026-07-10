from __future__ import annotations

from pydantic import BaseModel


class MechanicDefinition(BaseModel):
    mechanic_id: str
    canonical_name: str
    aliases: list[str] = []
    definition: str | None = None
    parent_category: str | None = None
    review_status: str = "human_verified"


class MechanicSet(BaseModel):
    mechanic_set_id: str
    mechanics: list[str]
    game_ids: list[str] = []
    source: str = "derived_from_game_ontology"
    attribution_level: str = "mechanic_set_inferred"
    confidence: float = 0.0
