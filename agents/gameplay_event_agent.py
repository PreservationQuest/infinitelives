"""Gameplay Event Agent v2 — Multi-source, reliability-scored."""
import logging, re, sys
from pathlib import Path
from typing import Optional
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from agents.base_agent import BaseAgent, AgentQuery
from scrapers.multi_source import MultiSourceScraper, ScrapedPage
from extractors.gameplay_event_extractor import GameplayEventExtractor
from utils.mda_fallback import MDAFallback
from models.schemas import (AgentResponse, GameplayEvent, GameplaySequence, GameMechanic,
                            WalkthroughMetadata, ConfidenceLevel, ReliabilityScore)

logger = logging.getLogger(__name__)
GAMEPLAY_KEYWORDS = ["mechanic","mechanics","gameplay","walkthrough","guide","combat","puzzle","boss",
    "dungeon","level","quest","player","skill","movement","crafting","stealth","strategy",
    "action","interaction","control","ability","fail","death","retry","explore","exploration",
    "discover","collect","dynamic","loop","feedback","difficulty","mda","aesthetic","sensation",
    "challenge","fellowship"]

def slugify(title):
    s = re.sub(r"[':!?,.\-()]", "", title.lower().strip())
    return re.sub(r"-+", "-", re.sub(r"\s+", "-", s)).strip("-")

class GameplayEventAgent(BaseAgent):
    def __init__(self, anthropic_api_key=None, model="claude-sonnet-4-20250514",
                 scraper=None, extractor=None, mda_fallback=None):
        self.scraper = scraper or MultiSourceScraper()
        self.extractor = extractor or GameplayEventExtractor(api_key=anthropic_api_key, model=model)
        self.mda_fallback = mda_fallback or MDAFallback()

    def get_name(self): return "gameplay_event_agent"

    def can_handle(self, query):
        text = query.query_text.lower()
        matches = sum(1 for kw in GAMEPLAY_KEYWORDS if kw in text)
        score = min(matches / 3.0, 1.0)
        if query.game_title: score = min(score + 0.2, 1.0)
        if query.genre.lower() in {"action","adventure","rpg","strategy","puzzle","simulation","visual_novel","walking_simulator"}:
            score = min(score + 0.1, 1.0)
        return score

    def retrieve(self, query):
        game_title = query.game_title
        game_slug = query.game_slug or slugify(game_title)
        logger.info(f"Agent processing: '{game_title}' (slug: {game_slug})")

        # Multi-source scraping
        pages = self.scraper.scrape_game(
            game_title=game_title, game_slug=game_slug,
            fandom_wiki=query.fandom_wiki, max_pages_per_source=5
        )

        all_events, all_sequences = [], []
        sources_used = list(set(p.source_name for p in pages))
        metadata = None

        if pages:
            metadata = WalkthroughMetadata(
                game_title=game_title, game_slug=game_slug,
                page_url=pages[0].url, source_name=", ".join(sources_used),
                section_titles=[p.title for p in pages],
                total_sections=len(pages), word_count=sum(p.word_count for p in pages))

            self.extractor.reset_registry()
            for page in pages:
                events = self.extractor.extract_from_text(
                    game_title, page.content_text, page.url, page.source_name)
                all_events.extend(events)
                if events:
                    all_sequences.append(self.extractor.build_sequence(
                        game_title, page.title, events, page.url))

        fallback_used = False
        if len(all_events) < 3 and query.include_fallback:
            logger.info(f"Sparse data, using MDA fallback")
            all_events.extend(self.mda_fallback.generate_fallback_events(game_title, query.genre or "action"))
            fallback_used = True

        all_mechanics = self.extractor.get_all_mechanics()
        if fallback_used:
            for e in all_events:
                for m in e.mechanics_involved:
                    if m not in all_mechanics: all_mechanics.append(m)

        kg_nodes = [m.to_kg_node() for m in all_mechanics] + [e.to_kg_node() for e in all_events]
        kg_edges = []
        for seq in all_sequences: kg_edges.extend(seq.to_kg_edges())
        for m in all_mechanics:
            kg_edges.append({"from": {"type": "Game", "name": game_title},
                           "relation": "contains_mechanic", "to": {"type": "Mechanic", "id": m.mechanic_id}})

        if fallback_used and not pages: confidence = ConfidenceLevel.LOW
        elif fallback_used: confidence = ConfidenceLevel.MEDIUM
        elif len(all_events) >= 5: confidence = ConfidenceLevel.HIGH
        else: confidence = ConfidenceLevel.MEDIUM

        # Compute overall reliability
        event_reliabilities = [e.reliability for e in all_events if e.reliability]
        overall_reliability = None
        if event_reliabilities:
            overall_reliability = ReliabilityScore(
                source_quality=sum(r.source_quality for r in event_reliabilities) / len(event_reliabilities),
                extraction_completeness=sum(r.extraction_completeness for r in event_reliabilities) / len(event_reliabilities),
                hallucination_risk=sum(r.hallucination_risk for r in event_reliabilities) / len(event_reliabilities),
                content_type_match=sum(r.content_type_match for r in event_reliabilities) / len(event_reliabilities),
            )
            overall_reliability.compute()

        return AgentResponse(
            agent_name=self.get_name(), query=query.query_text, game_title=game_title,
            events=all_events, sequences=all_sequences, mechanics=all_mechanics,
            kg_nodes=kg_nodes, kg_edges=kg_edges, confidence=confidence,
            fallback_used=fallback_used, source_urls=[p.url for p in pages],
            sources_used=sources_used, metadata=metadata,
            reliability=overall_reliability,
            token_usage=self.extractor.get_token_usage())

    def retrieve_from_text(self, game_title, text, genre="action", source_url="", source_name="local"):
        self.extractor.reset_registry()
        events = self.extractor.extract_from_text(game_title, text, source_url, source_name)
        all_mechanics = self.extractor.get_all_mechanics()
        fallback_used = False
        if len(events) < 3:
            events.extend(self.mda_fallback.generate_fallback_events(game_title, genre))
            fallback_used = True
        sequences = [self.extractor.build_sequence(game_title, "Full Walkthrough", events, source_url)] if events else []
        kg_nodes = [m.to_kg_node() for m in all_mechanics] + [e.to_kg_node() for e in events]
        kg_edges = []
        for s in sequences: kg_edges.extend(s.to_kg_edges())

        event_reliabilities = [e.reliability for e in events if e.reliability]
        overall_reliability = None
        if event_reliabilities:
            overall_reliability = ReliabilityScore(
                source_quality=sum(r.source_quality for r in event_reliabilities) / len(event_reliabilities),
                extraction_completeness=sum(r.extraction_completeness for r in event_reliabilities) / len(event_reliabilities),
                hallucination_risk=sum(r.hallucination_risk for r in event_reliabilities) / len(event_reliabilities),
                content_type_match=sum(r.content_type_match for r in event_reliabilities) / len(event_reliabilities),
            )
            overall_reliability.compute()

        return AgentResponse(
            agent_name=self.get_name(), query=f"Extract gameplay events from {game_title}",
            game_title=game_title, events=events, sequences=sequences, mechanics=all_mechanics,
            kg_nodes=kg_nodes, kg_edges=kg_edges,
            confidence=ConfidenceLevel.LOW if fallback_used else ConfidenceLevel.MEDIUM,
            fallback_used=fallback_used, source_urls=[source_url] if source_url else [],
            sources_used=[source_name], reliability=overall_reliability,
            token_usage=self.extractor.get_token_usage())

    def health_check(self): return self.scraper is not None and self.extractor is not None
