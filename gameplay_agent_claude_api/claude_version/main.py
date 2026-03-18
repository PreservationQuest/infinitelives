"""Gameplay Event Agent - CLI Entry Point."""
import argparse, json, logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, LOG_LEVEL
from agents.gameplay_event_agent import GameplayEventAgent
from agents.base_agent import AgentQuery

logging.basicConfig(level=getattr(logging, LOG_LEVEL), format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

DEMO_WALKTHROUGH = """
## The Great Plateau
You wake up in the Shrine of Resurrection. Pick up the Sheikah Slate from the pedestal.
Exit the shrine and head outside. You can see the vast world of Hyrule stretching before you.
Talk to the Old Man at the campfire. He will point you toward the first objective.
Pick up a tree branch or axe nearby as a weapon. You can also grab an apple from the trees.

## Shrine: Magnesis Trial
Enter the shrine. Use the Magnesis rune to grab metal objects and move them.
First, lift the metal plates off the floor to reveal a path. Then use Magnesis
to pull the metal block and create a bridge across the gap.
Fight the Guardian Scout at the end. Dodge its attacks and strike when it pauses.
Open the chest for a reward, then examine the altar.

## Combat: Bokoblin Camp
Approach the Bokoblin camp carefully. You can use stealth to sneak up,
or throw a bomb from distance. The red Bokoblins are weak and go down in 2-3 hits.
Watch out for the blue Bokoblin - it has more health and hits harder.
If you die, you respawn at the last autosave. The game autosaves frequently near shrines and towers.
Loot the camp for food, weapons, and materials. Cook food at the cooking pot
to restore hearts. Combine ingredients for stat-boosting meals.

## Boss: Stone Talus
The Stone Talus emerges from the ground. Climb onto its back and hit the
ore deposit on top. When it shakes you off, use the terrain to get above it.
Bomb arrows are very effective but expensive. Save them for harder fights.
If you fall off, dodge its slam attacks and try to climb back up. The fight
tests your stamina management and timing.
"""

def cmd_demo(args):
    print("=" * 60)
    print("GAMEPLAY EVENT AGENT - DEMO")
    print("Using built-in Zelda-style walkthrough sample")
    print("=" * 60)
    if not ANTHROPIC_API_KEY:
        print("\nNote: ANTHROPIC_API_KEY not set. Running with MDA fallback only.\n")
        agent = GameplayEventAgent(anthropic_api_key="demo-key")
        from utils.mda_fallback import MDAFallback
        fallback = MDAFallback()
        events = fallback.generate_fallback_events("The Legend of Zelda: Breath of the Wild", "adventure")
        print(f"MDA Fallback generated {len(events)} events:")
        for e in events:
            print(f"\n  {e.description}")
            for m in e.mechanics_involved: print(f"    Mechanic: {m.name} ({m.mechanic_type.value})")
            print(f"    Dynamics: {', '.join(d.value for d in e.dynamics)}")
            print(f"    Aesthetics: {', '.join(a.value for a in e.aesthetics)}")
        print(f"\n  Confidence: LOW (genre fallback)")
        return
    agent = GameplayEventAgent(anthropic_api_key=ANTHROPIC_API_KEY, model=CLAUDE_MODEL)
    response = agent.retrieve_from_text("The Legend of Zelda: Breath of the Wild", DEMO_WALKTHROUGH, "adventure", "https://www.neoseeker.com/the-legend-of-zelda-breath-of-the-wild/walkthrough")
    print(f"\nExtraction Results:")
    print(f"  Events:     {len(response.events)}")
    print(f"  Mechanics:  {len(response.mechanics)}")
    print(f"  KG Nodes:   {len(response.kg_nodes)}")
    print(f"  KG Edges:   {len(response.kg_edges)}")
    print(f"  Confidence: {response.confidence.value}")
    print(f"  Fallback:   {response.fallback_used}")
    print(f"\nMechanics:")
    for m in response.mechanics: print(f"  - {m.name} ({m.mechanic_type.value})")
    print(f"\nEvents:")
    for e in response.events[:8]:
        print(f"\n  [{e.section}] {e.description[:100]}")
        if e.dynamics: print(f"    Dynamics: {', '.join(d.value for d in e.dynamics)}")
        if e.player_actions: print(f"    Actions: {', '.join(e.player_actions[:3])}")
    print(f"\nWorking Memory Entry (for Multi-Hop Controller):")
    print(json.dumps(response.to_working_memory_entry(), indent=2, default=str))

def main():
    parser = argparse.ArgumentParser(description="Gameplay Event Agent - Infinite Lives")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("demo", help="Run demo with sample data")
    p_query = sub.add_parser("query", help="Natural language query")
    p_query.add_argument("query"); p_query.add_argument("--game", required=True); p_query.add_argument("--genre", default="action")
    args = parser.parse_args()
    if args.command == "demo": cmd_demo(args)
    elif args.command == "query":
        if not ANTHROPIC_API_KEY: print("Error: ANTHROPIC_API_KEY not set."); sys.exit(1)
        agent = GameplayEventAgent(anthropic_api_key=ANTHROPIC_API_KEY, model=CLAUDE_MODEL)
        query = AgentQuery(query_text=args.query, game_title=args.game, genre=args.genre)
        score = agent.can_handle(query); print(f"Routing score: {score:.2f}")
        response = agent.retrieve(query)
        print(f"Events: {len(response.events)}, Confidence: {response.confidence.value}")
        for e in response.events[:5]:
            print(f"\n  {e.description}")
            if e.mechanics_involved: print(f"  Mechanics: {', '.join(m.name for m in e.mechanics_involved)}")
    else: parser.print_help()

if __name__ == "__main__": main()
