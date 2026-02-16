"""
Infinite Lives - Video Game Research RAG System
A production-ready RAG system for analyzing video game research papers.
"""

__version__ = "2.0.0"
__author__ = "Ashutosh Khatavkar"

from .config import Config
from .client import client
from .assistant import AssistantManager
from .processor import GameResearchProcessor

__all__ = [
    'Config',
    'client',
    'AssistantManager',
    'GameResearchProcessor',
]
