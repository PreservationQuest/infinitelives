"""Base Agent Interface for multi-agent architecture."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from models.schemas import AgentResponse

@dataclass
class AgentQuery:
    query_text: str
    game_title: str = ""
    game_slug: str = ""
    genre: str = ""
    platform: str = ""
    fandom_wiki: str = ""  # NEW: Fandom wiki subdomain
    section: Optional[str] = None
    context_from_memory: dict = field(default_factory=dict)
    max_results: int = 20
    include_fallback: bool = True

class BaseAgent(ABC):
    @abstractmethod
    def retrieve(self, query: AgentQuery) -> AgentResponse: pass
    @abstractmethod
    def can_handle(self, query: AgentQuery) -> float: pass
    @abstractmethod
    def get_name(self) -> str: pass
    def health_check(self) -> bool: return True
