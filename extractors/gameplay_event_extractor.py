"""
Gameplay Event Extractor v2 — Claude API.

Improvements over v1:
  - Content pre-classification (skip tabular/meta content)
  - Quote-first extraction to reduce hallucination
  - Controlled vocabulary for mechanic types
  - Reliability scoring per extraction
  - Token usage tracking for cost monitoring
  - JSON repair fallback for malformed responses
  - Meta-text stripping before extraction
"""
import json, hashlib, logging, re, sys, time
from pathlib import Path
from typing import Optional
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import anthropic
except ImportError:
    anthropic = None

from models.schemas import (
    GameplayEvent, GameMechanic, GameplaySequence,
    MechanicType, DynamicPattern, AestheticResponse,
    ConfidenceLevel, ReliabilityScore, ContentType,
)
from utils.content_classifier import classify_content, compute_source_quality, strip_meta_content

logger = logging.getLogger(__name__)

# Enhanced system prompt with hallucination guards
EXTRACTION_SYSTEM_PROMPT = """You are an expert game analyst specializing in the MDA framework (Mechanics, Dynamics, Aesthetics).

CRITICAL RULES:
1. ONLY extract events that are EXPLICITLY described in the text. Do NOT infer or hallucinate mechanics not mentioned.
2. If the text does not describe gameplay events (e.g., it's just a list of items), return {"events": []}.
3. For each event, include a "source_quote" field with the exact phrase from the text that supports it.
4. Use ONLY these mechanic types: movement, combat, puzzle, resource_management, social, exploration, crafting, stealth, narrative_choice, time_based, collection, progression, environmental_observation, route_selection, relationship_change, other.
5. Use ONLY these dynamics: skill_loop, failure_retry, strategy_evolution, risk_reward, resource_tension, exploration_discovery, social_coordination, feedback_escalation, mastery_curve, emergent_narrative.
6. Use ONLY these aesthetics: sensation, fantasy, narrative, challenge, fellowship, discovery, expression, submission.

Respond ONLY with valid JSON. No markdown fences."""

EXTRACTION_USER_PROMPT = """Analyze this walkthrough for: "{game_title}" | Section: "{section}"

TEXT:
{text}

Extract as JSON:
{{"events": [{{"description": "...", "source_quote": "exact phrase from text supporting this event", "mechanics": [{{"name": "...", "type": "one of the allowed types", "description": "..."}}], "dynamics": ["from allowed list"], "aesthetics": ["from allowed list"], "player_actions": [], "failure_states": [], "strategy_hints": []}}]}}"""

MAX_CHUNK_TOKENS = 2000
CHARS_PER_TOKEN = 4


def chunk_text(text: str, max_chars: int = MAX_CHUNK_TOKENS * CHARS_PER_TOKEN) -> list[dict]:
    """Split text at section boundaries."""
    sections = re.split(r"(^##\s+.+$)", text, flags=re.MULTILINE)
    chunks, section, current = [], "Introduction", ""
    for part in sections:
        if part.startswith("## "):
            if current.strip() and len(current.strip()) > 100:
                chunks.append({"section": section, "text": current.strip()})
            section = part.replace("## ", "").strip()
            current = ""
        else:
            current += part
    if current.strip() and len(current.strip()) > 100:
        chunks.append({"section": section, "text": current.strip()})

    # Split oversized chunks
    final = []
    for c in chunks:
        if len(c["text"]) > max_chars:
            sub = ""
            for p in c["text"].split("\n\n"):
                if len(sub) + len(p) > max_chars:
                    if sub: final.append({"section": c["section"], "text": sub.strip()})
                    sub = p
                else:
                    sub += "\n\n" + p
            if sub.strip(): final.append({"section": c["section"], "text": sub.strip()})
        else:
            final.append(c)
    return final


def parse_mechanic_type(s):
    try: return MechanicType(s.lower().strip())
    except: return MechanicType.OTHER

def parse_dynamic(s):
    try: return DynamicPattern(s.lower().strip())
    except: return None

def parse_aesthetic(s):
    try: return AestheticResponse(s.lower().strip())
    except: return None

def try_repair_json(text: str) -> Optional[dict]:
    """Attempt to repair malformed JSON from LLM output."""
    # Strip markdown fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    text = text.strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fix trailing commas
    text = re.sub(r",\s*([}\]])", r"\1", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


class GameplayEventExtractor:
    """Enhanced LLM-powered extractor with pre-filtering and reliability scoring."""

    def __init__(self, api_key=None, model="claude-sonnet-4-20250514", max_retries=3):
        if anthropic is None:
            self.client = None
            logger.warning("anthropic package not installed. LLM extraction disabled.")
        else:
            self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.model = model
        self.max_retries = max_retries
        self._mechanic_registry = {}
        self._total_input_tokens = 0
        self._total_output_tokens = 0

    def _call_llm(self, game_title: str, section: str, text: str) -> Optional[dict]:
        """Call Claude with extraction prompt."""
        if self.client is None:
            logger.warning("No Anthropic client. Skipping.")
            return None

        user_prompt = EXTRACTION_USER_PROMPT.format(
            game_title=game_title, section=section,
            text=text[:MAX_CHUNK_TOKENS * CHARS_PER_TOKEN]
        )

        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model, max_tokens=2000,
                    system=EXTRACTION_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": user_prompt}],
                    temperature=0.1,
                )

                # Track token usage
                if hasattr(response, "usage"):
                    self._total_input_tokens += response.usage.input_tokens
                    self._total_output_tokens += response.usage.output_tokens

                content = response.content[0].text
                result = try_repair_json(content)
                if result:
                    return result
                else:
                    logger.warning(f"JSON repair failed on attempt {attempt+1}")

            except json.JSONDecodeError as e:
                logger.warning(f"JSON error attempt {attempt+1}: {e}")
            except Exception as e:
                logger.error(f"LLM call failed attempt {attempt+1}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
        return None

    def _make_mechanic_id(self, name, game_title):
        return f"mech_{hashlib.md5(f'{game_title}:{name}'.lower().encode()).hexdigest()[:12]}"

    def _make_event_id(self, game_title, section, idx):
        return f"evt_{hashlib.md5(f'{game_title}:{section}:{idx}'.encode()).hexdigest()[:12]}"

    def _compute_extraction_reliability(self, raw_event: dict, source_text: str, content_type: ContentType) -> ReliabilityScore:
        """Compute reliability score for a single extraction."""
        r = ReliabilityScore()

        # Source quality
        r.source_quality = compute_source_quality(source_text, content_type)

        # Extraction completeness (how many fields populated)
        fields_total = 6  # mechanics, dynamics, aesthetics, player_actions, failure_states, strategy_hints
        filled = 0
        if raw_event.get("mechanics"): filled += 1
        if raw_event.get("dynamics"): filled += 1
        if raw_event.get("aesthetics"): filled += 1
        if raw_event.get("player_actions"): filled += 1
        if raw_event.get("failure_states"): filled += 1
        if raw_event.get("strategy_hints"): filled += 1
        r.extraction_completeness = filled / fields_total

        # Hallucination risk (higher if no source_quote or quote not in text)
        quote = raw_event.get("source_quote", "")
        if quote and quote.lower() in source_text.lower():
            r.hallucination_risk = 0.1  # Very low risk
        elif quote:
            r.hallucination_risk = 0.4  # Quote present but not found verbatim
        else:
            r.hallucination_risk = 0.6  # No quote provided

        # Content type match
        r.content_type_match = {
            ContentType.NARRATIVE: 1.0,
            ContentType.MIXED: 0.6,
            ContentType.TABULAR: 0.2,
            ContentType.META: 0.1,
            ContentType.INSUFFICIENT: 0.0,
        }.get(content_type, 0.5)

        r.compute()
        return r

    def _parse_event(self, raw, game_title, section, order, source_url, source_text, source_name, content_type):
        mechs = []
        for m in raw.get("mechanics", []):
            name = m.get("name", "unknown")
            mid = self._make_mechanic_id(name, game_title)
            if mid in self._mechanic_registry:
                mechs.append(self._mechanic_registry[mid])
            else:
                mech = GameMechanic(
                    mechanic_id=mid, name=name,
                    mechanic_type=parse_mechanic_type(m.get("type", "other")),
                    description=m.get("description", ""),
                    source_url=source_url, source_text=source_text[:300],
                    source_name=source_name,
                    confidence=ConfidenceLevel.MEDIUM,
                    mda_tags=[m.get("type", "other")],
                )
                self._mechanic_registry[mid] = mech
                mechs.append(mech)

        reliability = self._compute_extraction_reliability(raw, source_text, content_type)

        return GameplayEvent(
            event_id=self._make_event_id(game_title, section, order),
            game_title=game_title, section=section, sequence_order=order,
            description=raw.get("description", ""),
            mechanics_involved=mechs,
            dynamics=[d for d in (parse_dynamic(x) for x in raw.get("dynamics", [])) if d],
            aesthetics=[a for a in (parse_aesthetic(x) for x in raw.get("aesthetics", [])) if a],
            player_actions=raw.get("player_actions", []),
            failure_states=raw.get("failure_states", []),
            strategy_hints=raw.get("strategy_hints", []),
            source_url=source_url, source_text=source_text[:500],
            source_name=source_name,
            confidence=ConfidenceLevel.MEDIUM,
            reliability=reliability,
        )

    def extract_from_text(self, game_title: str, text: str,
                         source_url: str = "", source_name: str = "") -> list[GameplayEvent]:
        """Extract events with content pre-filtering."""
        # Strip meta content first
        text = strip_meta_content(text)

        chunks = chunk_text(text)
        all_events = []
        order = 0
        skipped_chunks = 0

        logger.info(f"Extracting from {len(chunks)} chunks for '{game_title}'")

        for chunk in chunks:
            # PRE-FILTER: classify content before sending to LLM
            content_type = classify_content(chunk["text"])

            if content_type in (ContentType.INSUFFICIENT, ContentType.META):
                logger.debug(f"Skipping {content_type.value} chunk: {chunk['section']}")
                skipped_chunks += 1
                continue

            if content_type == ContentType.TABULAR:
                logger.debug(f"Skipping tabular chunk: {chunk['section']}")
                skipped_chunks += 1
                continue

            result = self._call_llm(game_title, chunk["section"], chunk["text"])
            if not result or "events" not in result:
                logger.warning(f"No events from: {chunk['section']}")
                continue

            for raw in result["events"]:
                event = self._parse_event(
                    raw, game_title, chunk["section"], order,
                    source_url, chunk["text"], source_name, content_type
                )
                all_events.append(event)
                order += 1

        logger.info(
            f"Extracted {len(all_events)} events, {len(self._mechanic_registry)} mechanics, "
            f"skipped {skipped_chunks} non-narrative chunks"
        )
        return all_events

    def build_sequence(self, game_title, section_name, events, source_url=""):
        return GameplaySequence(
            sequence_id=f"seq_{hashlib.md5(f'{game_title}:{section_name}'.encode()).hexdigest()[:12]}",
            game_title=game_title, section_name=section_name, events=events,
            overall_dynamics=list(set(d for e in events for d in e.dynamics)),
            overall_aesthetics=list(set(a for e in events for a in e.aesthetics)),
            source_url=source_url,
        )

    def get_all_mechanics(self): return list(self._mechanic_registry.values())
    def reset_registry(self): self._mechanic_registry.clear()

    def get_token_usage(self) -> dict:
        """Return cumulative token usage for cost tracking."""
        return {
            "total_input_tokens": self._total_input_tokens,
            "total_output_tokens": self._total_output_tokens,
            "estimated_cost_usd": round(
                (self._total_input_tokens / 1_000_000) * 3 +
                (self._total_output_tokens / 1_000_000) * 15, 4
            ),
        }
