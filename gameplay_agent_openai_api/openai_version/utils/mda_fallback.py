"""MDA Similarity Fallback for sparse walkthrough data."""
import json, logging, re, sys
from pathlib import Path
from typing import Optional
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from models.schemas import GameMechanic, GameplayEvent, MechanicType, DynamicPattern, AestheticResponse, ConfidenceLevel

logger = logging.getLogger(__name__)
MDA_DATASET_PATH = Path(__file__).parent.parent / "data" / "mda_dataset.json"

GENRE_MDA_DEFAULTS = {
    "action": {"mechanics": [("combat", MechanicType.COMBAT), ("movement", MechanicType.MOVEMENT), ("resource management", MechanicType.RESOURCE_MANAGEMENT)], "dynamics": [DynamicPattern.SKILL_LOOP, DynamicPattern.FAILURE_RETRY, DynamicPattern.RISK_REWARD], "aesthetics": [AestheticResponse.CHALLENGE, AestheticResponse.SENSATION]},
    "adventure": {"mechanics": [("exploration", MechanicType.EXPLORATION), ("puzzle solving", MechanicType.PUZZLE), ("narrative choices", MechanicType.NARRATIVE_CHOICE)], "dynamics": [DynamicPattern.EXPLORATION_DISCOVERY, DynamicPattern.EMERGENT_NARRATIVE], "aesthetics": [AestheticResponse.DISCOVERY, AestheticResponse.NARRATIVE, AestheticResponse.FANTASY]},
    "rpg": {"mechanics": [("combat", MechanicType.COMBAT), ("character progression", MechanicType.PROGRESSION), ("resource management", MechanicType.RESOURCE_MANAGEMENT), ("exploration", MechanicType.EXPLORATION)], "dynamics": [DynamicPattern.MASTERY_CURVE, DynamicPattern.STRATEGY_EVOLUTION, DynamicPattern.RISK_REWARD], "aesthetics": [AestheticResponse.FANTASY, AestheticResponse.CHALLENGE, AestheticResponse.DISCOVERY]},
    "puzzle": {"mechanics": [("puzzle solving", MechanicType.PUZZLE)], "dynamics": [DynamicPattern.MASTERY_CURVE, DynamicPattern.SKILL_LOOP], "aesthetics": [AestheticResponse.CHALLENGE, AestheticResponse.DISCOVERY]},
    "strategy": {"mechanics": [("resource management", MechanicType.RESOURCE_MANAGEMENT), ("tactical combat", MechanicType.COMBAT)], "dynamics": [DynamicPattern.STRATEGY_EVOLUTION, DynamicPattern.RESOURCE_TENSION], "aesthetics": [AestheticResponse.CHALLENGE, AestheticResponse.EXPRESSION]},
    "simulation": {"mechanics": [("resource management", MechanicType.RESOURCE_MANAGEMENT), ("crafting", MechanicType.CRAFTING), ("exploration", MechanicType.EXPLORATION)], "dynamics": [DynamicPattern.EMERGENT_NARRATIVE, DynamicPattern.EXPLORATION_DISCOVERY], "aesthetics": [AestheticResponse.EXPRESSION, AestheticResponse.DISCOVERY]},
    "social": {"mechanics": [("social interaction", MechanicType.SOCIAL), ("GPS movement", MechanicType.MOVEMENT), ("collection", MechanicType.COLLECTION)], "dynamics": [DynamicPattern.SOCIAL_COORDINATION, DynamicPattern.EXPLORATION_DISCOVERY], "aesthetics": [AestheticResponse.FELLOWSHIP, AestheticResponse.DISCOVERY]},
}

class MDAFallback:
    def __init__(self, mda_dataset_path=None):
        self.dataset = {}; self.dataset_path = mda_dataset_path or MDA_DATASET_PATH; self._load_dataset()
    def _load_dataset(self):
        if self.dataset_path.exists():
            try:
                with open(self.dataset_path) as f: self.dataset = json.load(f)
                logger.info(f"Loaded MDA dataset: {len(self.dataset)} games")
            except Exception as e: logger.warning(f"Could not load MDA dataset: {e}")
    def get_game_mda(self, game_title):
        n = game_title.lower().strip()
        for key, data in self.dataset.items():
            if key.lower() == n or data.get("title","").lower() == n: return data
            s = re.sub(r"[^a-z0-9\s]", "", n); s = re.sub(r"\s+", "-", s).strip("-")
            if key.lower() == s: return data
        return None
    def get_genre_defaults(self, genre):
        g = genre.lower().strip()
        if g in GENRE_MDA_DEFAULTS: return GENRE_MDA_DEFAULTS[g]
        for k, v in GENRE_MDA_DEFAULTS.items():
            if k in g or g in k: return v
        return GENRE_MDA_DEFAULTS.get("action", {})
    def generate_fallback_events(self, game_title, genre="action"):
        gm = self.get_game_mda(game_title)
        if gm: return self._from_game_mda(game_title, gm)
        return self._from_genre_defaults(game_title, genre, self.get_genre_defaults(genre))
    def _from_game_mda(self, game_title, mda_data):
        mechs = [GameMechanic(mechanic_id=f"mda_mech_{hash(m.get('name',''))%100000:05d}", name=m.get("name",""), mechanic_type=MechanicType(m.get("type","other")), description=m.get("description",""), confidence=ConfidenceLevel.LOW) for m in mda_data.get("mechanics",[])]
        dynamics = []
        for d in mda_data.get("dynamics",[]):
            try: dynamics.append(DynamicPattern(d))
            except ValueError: pass
        aesthetics = []
        for a in mda_data.get("aesthetics",[]):
            try: aesthetics.append(AestheticResponse(a))
            except ValueError: pass
        return [GameplayEvent(event_id=f"fallback_{hash(game_title)%100000:05d}", game_title=game_title, section="MDA Fallback (no walkthrough data)", sequence_order=0, description=f"Inferred gameplay profile for {game_title} from MDA dataset", mechanics_involved=mechs, dynamics=dynamics, aesthetics=aesthetics, confidence=ConfidenceLevel.LOW)]
    def _from_genre_defaults(self, game_title, genre, defaults):
        mechs = [GameMechanic(mechanic_id=f"genre_mech_{hash(n)%100000:05d}", name=n, mechanic_type=mt, description=f"Typical {genre} mechanic", confidence=ConfidenceLevel.LOW) for n, mt in defaults.get("mechanics",[])]
        return [GameplayEvent(event_id=f"genre_fallback_{hash(game_title)%100000:05d}", game_title=game_title, section=f"Genre Fallback ({genre})", sequence_order=0, description=f"Inferred gameplay profile for {game_title} based on {genre} genre defaults", mechanics_involved=mechs, dynamics=defaults.get("dynamics",[]), aesthetics=defaults.get("aesthetics",[]), confidence=ConfidenceLevel.LOW)]
