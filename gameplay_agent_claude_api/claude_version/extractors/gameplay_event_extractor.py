"""Gameplay Event Extractor - Claude (Anthropic) API version."""
import json, hashlib, logging, re, sys
from pathlib import Path
from typing import Optional
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    import anthropic
except ImportError:
    anthropic = None

from models.schemas import GameplayEvent, GameMechanic, GameplaySequence, MechanicType, DynamicPattern, AestheticResponse, ConfidenceLevel

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are an expert game analyst specializing in the MDA framework (Mechanics, Dynamics, Aesthetics). Extract structured gameplay events from walkthrough text.
For each segment extract: 1) Mechanics - concrete rules/actions 2) Dynamics - emergent patterns 3) Aesthetics - emotional responses 4) Player Actions 5) Failure States 6) Strategy Hints.
Respond ONLY with valid JSON. No markdown fences, no explanation."""

EXTRACTION_USER_PROMPT = """Analyze this walkthrough text for game: "{game_title}"
Section: "{section}"
TEXT:
{text}

Extract gameplay events as JSON:
{{"events": [{{"description": "...", "mechanics": [{{"name": "...", "type": "movement|combat|puzzle|resource_management|social|exploration|crafting|stealth|narrative_choice|time_based|collection|progression|other", "description": "..."}}], "dynamics": ["skill_loop|failure_retry|strategy_evolution|risk_reward|resource_tension|exploration_discovery|social_coordination|feedback_escalation|mastery_curve|emergent_narrative"], "aesthetics": ["sensation|fantasy|narrative|challenge|fellowship|discovery|expression|submission"], "player_actions": [], "failure_states": [], "strategy_hints": []}}]}}"""

MAX_CHUNK_TOKENS = 2000
CHARS_PER_TOKEN = 4

def chunk_text(text, max_chars=MAX_CHUNK_TOKENS*CHARS_PER_TOKEN):
    sections = re.split(r"(^##\s+.+$)", text, flags=re.MULTILINE)
    chunks, current_section, current_text = [], "Introduction", ""
    for part in sections:
        if part.startswith("## "):
            if current_text.strip() and len(current_text.strip()) > 100: chunks.append({"section": current_section, "text": current_text.strip()})
            current_section = part.replace("## ", "").strip(); current_text = ""
        else: current_text += part
    if current_text.strip() and len(current_text.strip()) > 100: chunks.append({"section": current_section, "text": current_text.strip()})
    final = []
    for c in chunks:
        if len(c["text"]) > max_chars:
            sub = ""
            for p in c["text"].split("\n\n"):
                if len(sub) + len(p) > max_chars:
                    if sub: final.append({"section": c["section"], "text": sub.strip()})
                    sub = p
                else: sub += "\n\n" + p
            if sub.strip(): final.append({"section": c["section"], "text": sub.strip()})
        else: final.append(c)
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

class GameplayEventExtractor:
    def __init__(self, api_key=None, model="claude-sonnet-4-20250514", max_retries=3):
        if anthropic is None:
            self.client = None; logger.warning("anthropic package not installed. LLM extraction disabled.")
        else:
            self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self.model = model; self.max_retries = max_retries; self._mechanic_registry = {}

    def _call_llm(self, game_title, section, text):
        if self.client is None: logger.warning("No Anthropic client. Skipping."); return None
        user_prompt = EXTRACTION_USER_PROMPT.format(game_title=game_title, section=section, text=text[:MAX_CHUNK_TOKENS*CHARS_PER_TOKEN])
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(model=self.model, max_tokens=2000, system=EXTRACTION_SYSTEM_PROMPT, messages=[{"role": "user", "content": user_prompt}], temperature=0.1)
                content = response.content[0].text
                content = re.sub(r"```json\s*", "", content); content = re.sub(r"```\s*$", "", content)
                return json.loads(content.strip())
            except json.JSONDecodeError as e: logger.warning(f"JSON parse error attempt {attempt+1}: {e}")
            except Exception as e:
                logger.error(f"LLM call failed attempt {attempt+1}: {e}")
                if attempt < self.max_retries - 1: import time; time.sleep(2**attempt)
        return None

    def _make_mechanic_id(self, name, game_title): return f"mech_{hashlib.md5(f'{game_title}:{name}'.lower().encode()).hexdigest()[:12]}"
    def _make_event_id(self, game_title, section, idx): return f"evt_{hashlib.md5(f'{game_title}:{section}:{idx}'.encode()).hexdigest()[:12]}"

    def _parse_event(self, raw, game_title, section, order, source_url, source_text):
        mechs = []
        for m in raw.get("mechanics", []):
            name = m.get("name", "unknown"); mid = self._make_mechanic_id(name, game_title)
            if mid in self._mechanic_registry: mechs.append(self._mechanic_registry[mid])
            else:
                mech = GameMechanic(mechanic_id=mid, name=name, mechanic_type=parse_mechanic_type(m.get("type","other")), description=m.get("description",""), source_url=source_url, source_text=source_text[:300], confidence=ConfidenceLevel.MEDIUM, mda_tags=[m.get("type","other")])
                self._mechanic_registry[mid] = mech; mechs.append(mech)
        return GameplayEvent(event_id=self._make_event_id(game_title, section, order), game_title=game_title, section=section, sequence_order=order, description=raw.get("description",""), mechanics_involved=mechs, dynamics=[d for d in (parse_dynamic(x) for x in raw.get("dynamics",[])) if d], aesthetics=[a for a in (parse_aesthetic(x) for x in raw.get("aesthetics",[])) if a], player_actions=raw.get("player_actions",[]), failure_states=raw.get("failure_states",[]), strategy_hints=raw.get("strategy_hints",[]), source_url=source_url, source_text=source_text[:500], confidence=ConfidenceLevel.MEDIUM)

    def extract_from_text(self, game_title, text, source_url=""):
        chunks = chunk_text(text); all_events = []; order = 0
        logger.info(f"Extracting from {len(chunks)} chunks for '{game_title}'")
        for chunk in chunks:
            result = self._call_llm(game_title, chunk["section"], chunk["text"])
            if not result or "events" not in result: logger.warning(f"No events from: {chunk['section']}"); continue
            for raw in result["events"]:
                all_events.append(self._parse_event(raw, game_title, chunk["section"], order, source_url, chunk["text"])); order += 1
        logger.info(f"Extracted {len(all_events)} events, {len(self._mechanic_registry)} unique mechanics")
        return all_events

    def build_sequence(self, game_title, section_name, events, source_url=""):
        return GameplaySequence(sequence_id=f"seq_{hashlib.md5(f'{game_title}:{section_name}'.encode()).hexdigest()[:12]}", game_title=game_title, section_name=section_name, events=events, overall_dynamics=list(set(d for e in events for d in e.dynamics)), overall_aesthetics=list(set(a for e in events for a in e.aesthetics)), source_url=source_url)

    def get_all_mechanics(self): return list(self._mechanic_registry.values())
    def reset_registry(self): self._mechanic_registry.clear()
