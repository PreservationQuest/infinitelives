from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from game_evidence_graph.schemas.evidence import ReviewStatus


class OntologyFeature(BaseModel):
    model_config = ConfigDict(extra="allow")

    mechanic_id: Optional[str] = None
    dynamic_id: Optional[str] = None
    aesthetic_id: Optional[str] = None
    mechanic_name: Optional[str] = None
    dynamic_name: Optional[str] = None
    aesthetic_name: Optional[str] = None
    source: str = "paper_text"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SourceQuote(BaseModel):
    model_config = ConfigDict(extra="allow")

    paper_id: str
    page: Optional[int] = None
    quote: str


class GameRecord(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    game_id: str
    game_name: Optional[str] = None
    canonical_game_name: str
    aliases: list[str] = []
    developer: Optional[str] = None
    publisher: Optional[str] = None
    release_year: Optional[int] = None
    genre: list[str] = []
    platform: list[str] = []
    mechanics: list[OntologyFeature] = []
    dynamics: list[OntologyFeature] = []
    aesthetics: list[OntologyFeature] = []
    core_gameplay_loop: Optional[str] = None
    gameplay_objective: Optional[str] = None
    player_perspective: Optional[str] = None
    multiplayer_type: Optional[str] = None
    progression_system: Optional[str] = None
    npc_interaction: Optional[str] = None
    procedural_generation: Optional[bool] = None
    world_persistence: Optional[bool] = None
    skill_requirement: Optional[str] = None
    cognitive_demands: list[str] = []
    social_features: list[str] = []
    communication_requirement: Optional[str] = None
    gameplay_summary: Optional[str] = None
    source_papers: list[str] = []
    source_quotes: list[SourceQuote] = []
    game_match_confidence: str = "needs_review"
    confidence_label: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    review_status: ReviewStatus = ReviewStatus.needs_review

    @model_validator(mode="before")
    @classmethod
    def accept_example_game_ontology_shape(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        if "canonical_game_name" not in normalized and "game_name" in normalized:
            normalized["canonical_game_name"] = normalized["game_name"]
        if "game_name" not in normalized and "canonical_game_name" in normalized:
            normalized["game_name"] = normalized["canonical_game_name"]

        confidence = normalized.get("confidence")
        if isinstance(confidence, str):
            normalized["confidence_label"] = confidence
            normalized["confidence"] = {
                "high": 0.90,
                "medium": 0.65,
                "low": 0.35,
                "needs_review": 0.20,
            }.get(confidence.strip().lower(), 0.0)

        return normalized

    @field_validator("mechanics", mode="before")
    @classmethod
    def accept_mechanic_names(cls, value: Any) -> Any:
        return _coerce_feature_list(value, "mechanic")

    @field_validator("dynamics", mode="before")
    @classmethod
    def accept_dynamic_names(cls, value: Any) -> Any:
        return _coerce_feature_list(value, "dynamic")

    @field_validator("aesthetics", mode="before")
    @classmethod
    def accept_aesthetic_names(cls, value: Any) -> Any:
        return _coerce_feature_list(value, "aesthetic")


class GameOntology(BaseModel):
    model_config = ConfigDict(extra="allow")

    games: list[GameRecord] = []


def _coerce_feature_list(value: Any, feature_type: str) -> Any:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]

    coerced: list[Any] = []
    id_key = f"{feature_type}_id"
    name_key = f"{feature_type}_name"
    for index, item in enumerate(value, start=1):
        if isinstance(item, str):
            coerced.append(
                {
                    id_key: f"{feature_type[0]}{index:03d}",
                    name_key: item,
                    "source": "seed_ontology",
                    "confidence": 0.90,
                }
            )
        else:
            coerced.append(item)
    return coerced
