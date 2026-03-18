"""
VG-KG Compatible Data Models for the Gameplay Event Agent.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from datetime import datetime

class MechanicType(Enum):
    MOVEMENT = "movement"
    COMBAT = "combat"
    PUZZLE = "puzzle"
    RESOURCE_MANAGEMENT = "resource_management"
    SOCIAL = "social"
    EXPLORATION = "exploration"
    CRAFTING = "crafting"
    STEALTH = "stealth"
    NARRATIVE_CHOICE = "narrative_choice"
    TIME_BASED = "time_based"
    COLLECTION = "collection"
    PROGRESSION = "progression"
    OTHER = "other"

class DynamicPattern(Enum):
    SKILL_LOOP = "skill_loop"
    FAILURE_RETRY = "failure_retry"
    STRATEGY_EVOLUTION = "strategy_evolution"
    RISK_REWARD = "risk_reward"
    RESOURCE_TENSION = "resource_tension"
    EXPLORATION_DISCOVERY = "exploration_discovery"
    SOCIAL_COORDINATION = "social_coordination"
    FEEDBACK_ESCALATION = "feedback_escalation"
    MASTERY_CURVE = "mastery_curve"
    EMERGENT_NARRATIVE = "emergent_narrative"

class AestheticResponse(Enum):
    SENSATION = "sensation"
    FANTASY = "fantasy"
    NARRATIVE = "narrative"
    CHALLENGE = "challenge"
    FELLOWSHIP = "fellowship"
    DISCOVERY = "discovery"
    EXPRESSION = "expression"
    SUBMISSION = "submission"

class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFERRED = "inferred"

@dataclass
class GameMechanic:
    mechanic_id: str
    name: str
    mechanic_type: MechanicType
    description: str
    source_text: str = ""
    source_url: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    mda_tags: list[str] = field(default_factory=list)

    def to_kg_node(self) -> dict:
        return {
            "entity_type": "Mechanic", "id": self.mechanic_id, "name": self.name,
            "type": self.mechanic_type.value, "description": self.description,
            "confidence": self.confidence.value, "mda_tags": self.mda_tags,
            "provenance": {"source": "gameplay_event_agent", "source_url": self.source_url, "source_text": self.source_text[:500]}
        }

@dataclass
class GameplayEvent:
    event_id: str
    game_title: str
    section: str
    sequence_order: int
    description: str
    mechanics_involved: list[GameMechanic] = field(default_factory=list)
    dynamics: list[DynamicPattern] = field(default_factory=list)
    aesthetics: list[AestheticResponse] = field(default_factory=list)
    player_actions: list[str] = field(default_factory=list)
    failure_states: list[str] = field(default_factory=list)
    strategy_hints: list[str] = field(default_factory=list)
    source_url: str = ""
    source_text: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    def to_kg_node(self) -> dict:
        return {
            "entity_type": "GameplayEvent", "id": self.event_id, "game": self.game_title,
            "section": self.section, "order": self.sequence_order, "description": self.description,
            "mechanics": [m.mechanic_id for m in self.mechanics_involved],
            "dynamics": [d.value for d in self.dynamics], "aesthetics": [a.value for a in self.aesthetics],
            "player_actions": self.player_actions, "failure_states": self.failure_states,
            "confidence": self.confidence.value,
            "provenance": {"source": "gameplay_event_agent", "source_url": self.source_url}
        }

@dataclass
class GameplaySequence:
    sequence_id: str
    game_title: str
    section_name: str
    events: list[GameplayEvent] = field(default_factory=list)
    overall_dynamics: list[DynamicPattern] = field(default_factory=list)
    overall_aesthetics: list[AestheticResponse] = field(default_factory=list)
    difficulty_curve: str = ""
    source_url: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_kg_edges(self) -> list[dict]:
        edges = [{"from": {"type": "Game", "name": self.game_title}, "relation": "has_sequence", "to": {"type": "GameplaySequence", "id": self.sequence_id}}]
        for event in self.events:
            edges.append({"from": {"type": "GameplaySequence", "id": self.sequence_id}, "relation": "contains_event", "to": {"type": "GameplayEvent", "id": event.event_id}})
            for m in event.mechanics_involved:
                edges.append({"from": {"type": "GameplayEvent", "id": event.event_id}, "relation": "involves_mechanic", "to": {"type": "Mechanic", "id": m.mechanic_id}})
            for d in event.dynamics:
                edges.append({"from": {"type": "GameplayEvent", "id": event.event_id}, "relation": "produces_dynamic", "to": {"type": "Dynamic", "name": d.value}})
            for a in event.aesthetics:
                edges.append({"from": {"type": "GameplayEvent", "id": event.event_id}, "relation": "evokes_aesthetic", "to": {"type": "Aesthetic", "name": a.value}})
        return edges

@dataclass
class WalkthroughMetadata:
    game_title: str
    game_slug: str
    platform: str = ""
    genre: str = ""
    page_title: str = ""
    page_url: str = ""
    section_titles: list[str] = field(default_factory=list)
    total_sections: int = 0
    word_count: int = 0
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass
class AgentResponse:
    agent_name: str = "gameplay_event_agent"
    query: str = ""
    game_title: str = ""
    events: list[GameplayEvent] = field(default_factory=list)
    sequences: list[GameplaySequence] = field(default_factory=list)
    mechanics: list[GameMechanic] = field(default_factory=list)
    kg_nodes: list[dict] = field(default_factory=list)
    kg_edges: list[dict] = field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    fallback_used: bool = False
    source_urls: list[str] = field(default_factory=list)
    metadata: Optional[WalkthroughMetadata] = None
    error: Optional[str] = None

    def to_working_memory_entry(self) -> dict:
        return {
            "agent": self.agent_name, "query": self.query, "game": self.game_title,
            "evidence_count": len(self.events),
            "mechanics_found": [m.name for m in self.mechanics],
            "dynamics_found": list(set(d.value for e in self.events for d in e.dynamics)),
            "confidence": self.confidence.value, "fallback_used": self.fallback_used,
            "source_urls": self.source_urls, "kg_nodes": self.kg_nodes, "kg_edges": self.kg_edges,
        }
