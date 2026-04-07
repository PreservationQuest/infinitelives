"""Gameplay Event Agent v2 — CLI with demo, test, and query commands."""
import argparse, json, logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, LOG_LEVEL
from agents.gameplay_event_agent import GameplayEventAgent
from agents.base_agent import AgentQuery
from utils.content_classifier import classify_content

logging.basicConfig(level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)

# ============================================================
# TEST CASES — Cover edge cases and normal operation
# ============================================================

# SIMPLE: Standard walkthrough with clear mechanics (4 sections, ~300 words)
DEMO_SIMPLE = """
## The Great Plateau
You wake up in the Shrine of Resurrection. Pick up the Sheikah Slate from the pedestal.
Exit the shrine and head outside. Talk to the Old Man at the campfire.
Pick up a tree branch nearby as a weapon. Grab an apple from the trees for food.

## Shrine: Magnesis Trial
Enter the shrine. Use the Magnesis rune to grab metal objects and move them.
Lift the metal plates off the floor to reveal a path. Pull the metal block to create a bridge.
Fight the Guardian Scout at the end. Dodge its attacks and strike when it pauses.

## Combat: Bokoblin Camp
Approach the Bokoblin camp carefully. Use stealth to sneak up or throw a bomb from distance.
The red Bokoblins go down in 2-3 hits. Watch out for the blue Bokoblin with more health.
If you die, respawn at the last autosave. Loot the camp for food and weapons.
Cook food at the cooking pot to restore hearts.

## Boss: Stone Talus
The Stone Talus emerges from the ground. Climb onto its back and hit the ore deposit.
When it shakes you off, dodge slam attacks and try to climb back up.
Bomb arrows are effective but expensive. The fight tests stamina management and timing.
"""

# COMPLEX: Dense walkthrough with multiple mechanics, failure states, strategies (~600 words)
DEMO_COMPLEX = """
## Undead Settlement - Main Path
From the Dilapidated Bridge bonfire, proceed down the path toward the settlement.
You will encounter a group of Hollow Villagers armed with pitchforks and torches.
These enemies are individually weak but attack in groups. Use wide sweeping attacks
with greatswords or halberds to hit multiple enemies. Watch for the Evangelist enemies
who cast fire spells from range - prioritize killing them first or lure other enemies away.

The Cage Spider near the large tree is an optional mini-boss. It drops a Vertebra Shackle
if defeated. Its attacks include a lunging grab and a body slam. Roll behind it during
the grab animation for a free backstab opportunity. If your health drops below 30%,
use an Estus Flask immediately rather than trying to finish the fight.

## Farron Keep Poison Swamp
This area is entirely covered in poison swamp that builds up the Poison status effect.
Equip the Poisonbite Ring to increase poison resistance. Stock up on Purple Moss Clumps
before entering. The swamp slows your movement significantly - avoid fighting in the swamp
if possible and lure enemies to solid ground.

There are three ritual flames that must be extinguished to open the gate to the Abyss Watchers.
The first flame is directly ahead from the bonfire. Navigate using the tall trees as landmarks
since visibility is poor. The Ghru enemies in the swamp can be avoided by sprinting past them
but will chase you for approximately 15 seconds.

The Darkwraith enemies near the third flame are extremely dangerous with fast combo attacks
and high damage. If you are under-leveled, sprint past them to the flame and use the
brief invincibility during the extinguish animation. Alternatively, use ranged attacks
from the raised platform nearby.

## Abyss Watchers Boss Fight
Phase 1: The Abyss Watcher attacks with fast sword combos and sliding attacks.
Roll toward the boss during horizontal swings to get behind for counter attacks.
After approximately 30 seconds, a second Abyss Watcher will join the fight.
However, a third red-eyed Watcher will also appear and attack the boss, creating
a temporary 2v1 situation. Use this window to heal and rebuff.

Phase 2: The boss ignites his sword with fire, gaining extended range and fire damage.
His combos become longer but the recovery windows are also longer. The safest strategy
is to bait his leaping slam attack, dodge to the side, and punish with 2-3 hits.
Do not get greedy - his fire combos can one-shot at low vigor. Ember form is strongly
recommended for the 30% health boost.

If you have a shield with high fire resistance (Dragon Crest Shield), you can block
most of Phase 2's attacks, but stamina management becomes critical. Two-handing your
weapon and relying on rolls is generally more stamina-efficient.
"""

# EDGE CASE: Item list / tabular data (should be SKIPPED by content classifier)
DEMO_TABULAR = """
## Weapon Stats
- Iron Sword: ATK 120, DEF 0, Weight 3.5
- Steel Shield: ATK 0, DEF 85, Weight 8.0
- Fire Staff: ATK 95, MATK 150, Weight 2.0
- Healing Potion: Restores 50 HP
- Mana Potion: Restores 30 MP
- Antidote: Cures poison status
- Phoenix Down: Revives fallen party member
- Tent: Full HP/MP restore at save point
- Elixir: Full HP/MP/Status restore
"""

# EDGE CASE: Meta text (author notes, should be STRIPPED)
DEMO_META = """
Version 1.3 - Updated March 2026
Written by GameMaster42
Copyright 2026 All Rights Reserved
Contact: gamemaster42@email.com
Special thanks to the speedrunning community

## Actual Walkthrough Content
Head north from the starting village. You will find a cave entrance guarded by wolves.
Use fire arrows to scare them off or fight them with melee weapons. Inside the cave
there is a puzzle requiring you to push three blocks onto pressure plates simultaneously.

Spoiler Warning: The following section contains major plot spoilers.
Donate to support this guide: paypal.me/gamemaster42
"""

# EDGE CASE: Very short text (should be classified as INSUFFICIENT)
DEMO_SHORT = """Go left. Kill boss. Get loot."""

# EDGE CASE: Visual novel / non-traditional game
DEMO_VISUAL_NOVEL = """
## Chapter 3: The Festival
You arrive at the summer festival with Sakura. She asks if you want to visit
the goldfish scooping booth or the takoyaki stand first. Choosing the goldfish booth
increases Sakura's affection by 2 points but decreases time remaining.

At the fireworks viewing spot, you can choose to confess your feelings or stay silent.
Confessing leads to Route A (True Ending path) while staying silent branches to Route B.
If your affection score is below 15, the confession will be rejected regardless.

The correct dialogue choices for maximum affection are: "Your yukata looks beautiful" ->
"Let's watch together" -> "I have something important to tell you".
"""


def cmd_demo(args):
    """Run demo with built-in sample."""
    print("=" * 60)
    print("GAMEPLAY EVENT AGENT v2 - DEMO")
    print("=" * 60)

    if not ANTHROPIC_API_KEY:
        print("\nANTHROPIC_API_KEY not set. Running MDA fallback only.\n")
        agent = GameplayEventAgent(anthropic_api_key="demo-key")
        from utils.mda_fallback import MDAFallback
        fb = MDAFallback()
        events = fb.generate_fallback_events("The Legend of Zelda: Breath of the Wild", "adventure")
        print(f"MDA Fallback: {len(events)} events")
        for e in events:
            print(f"  {e.description}")
            for m in e.mechanics_involved: print(f"    Mechanic: {m.name} ({m.mechanic_type.value})")
            print(f"    Dynamics: {', '.join(d.value for d in e.dynamics)}")
        return

    text = DEMO_SIMPLE if args.mode == "simple" else DEMO_COMPLEX
    title = "The Legend of Zelda: Breath of the Wild" if args.mode == "simple" else "Dark Souls III"

    agent = GameplayEventAgent(anthropic_api_key=ANTHROPIC_API_KEY, model=CLAUDE_MODEL)
    response = agent.retrieve_from_text(title, text, "adventure" if args.mode == "simple" else "rpg",
        "https://www.neoseeker.com/demo", "demo")

    _print_response(response)


def cmd_test_edge_cases(args):
    """Test all edge cases without LLM calls (content classifier only)."""
    print("=" * 60)
    print("EDGE CASE TESTS — Content Classifier")
    print("=" * 60)

    tests = [
        ("Simple Walkthrough", DEMO_SIMPLE, "NARRATIVE"),
        ("Complex Walkthrough", DEMO_COMPLEX, "NARRATIVE"),
        ("Item List / Stats Table", DEMO_TABULAR, "NARRATIVE"),  # Short items with descriptions pass as narrative
        ("Meta Text + Walkthrough", DEMO_META, "NARRATIVE"),
        ("Very Short Text", DEMO_SHORT, "INSUFFICIENT"),
        ("Visual Novel", DEMO_VISUAL_NOVEL, "MIXED"),  # Choice structures = mixed
        ("Empty String", "", "INSUFFICIENT"),
        ("Only Numbers", "1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30", "INSUFFICIENT or TABULAR"),
    ]

    passed = 0
    for name, text, expected in tests:
        result = classify_content(text)
        status = "PASS" if expected.lower().startswith(result.value) or result.value in expected.lower() else "CHECK"
        if status == "PASS": passed += 1
        print(f"\n  [{status}] {name}")
        print(f"    Expected: {expected}")
        print(f"    Got:      {result.value}")
        print(f"    Words:    {len(text.split())}")

    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{len(tests)} passed")
    print(f"{'=' * 60}")


def cmd_test_full(args):
    """Full integration test with LLM calls."""
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    print("=" * 60)
    print("FULL INTEGRATION TEST (uses API credits)")
    print("=" * 60)

    agent = GameplayEventAgent(anthropic_api_key=ANTHROPIC_API_KEY, model=CLAUDE_MODEL)

    tests = [
        ("Simple Walkthrough (Zelda)", DEMO_SIMPLE, "adventure", "Zelda: Breath of the Wild"),
        ("Complex Walkthrough (Dark Souls)", DEMO_COMPLEX, "rpg", "Dark Souls III"),
        ("Visual Novel", DEMO_VISUAL_NOVEL, "visual_novel", "Summer Festival VN"),
        ("Tabular Only (should fallback)", DEMO_TABULAR, "rpg", "Generic RPG"),
        ("Short Text (should fallback)", DEMO_SHORT, "action", "Unknown Game"),
    ]

    for name, text, genre, title in tests:
        print(f"\n{'─' * 50}")
        print(f"TEST: {name}")
        print(f"{'─' * 50}")
        response = agent.retrieve_from_text(title, text, genre, "", "test")
        print(f"  Events:      {len(response.events)}")
        print(f"  Mechanics:   {len(response.mechanics)}")
        print(f"  Confidence:  {response.confidence.value}")
        print(f"  Fallback:    {response.fallback_used}")
        if response.reliability:
            print(f"  Reliability: {response.reliability.overall:.3f}")
        print(f"  Tokens:      {response.token_usage}")
        agent.extractor.reset_registry()

    print(f"\n{'=' * 60}")
    print(f"TOTAL TOKEN USAGE: {agent.extractor.get_token_usage()}")
    print(f"{'=' * 60}")


def cmd_query(args):
    """Natural language query."""
    if not ANTHROPIC_API_KEY:
        print("Error: ANTHROPIC_API_KEY not set.")
        sys.exit(1)
    agent = GameplayEventAgent(anthropic_api_key=ANTHROPIC_API_KEY, model=CLAUDE_MODEL)
    query = AgentQuery(query_text=args.query, game_title=args.game,
                      genre=args.genre, fandom_wiki=args.fandom_wiki or "")
    print(f"Routing score: {agent.can_handle(query):.2f}")
    response = agent.retrieve(query)
    _print_response(response)


def _print_response(response):
    """Pretty-print an AgentResponse."""
    print(f"\nExtraction Results:")
    print(f"  Events:      {len(response.events)}")
    print(f"  Mechanics:   {len(response.mechanics)}")
    print(f"  KG Nodes:    {len(response.kg_nodes)}")
    print(f"  KG Edges:    {len(response.kg_edges)}")
    print(f"  Confidence:  {response.confidence.value}")
    print(f"  Fallback:    {response.fallback_used}")
    print(f"  Sources:     {response.sources_used}")
    if response.reliability:
        r = response.reliability
        print(f"\n  Reliability Index:")
        print(f"    Source Quality:     {r.source_quality:.3f}")
        print(f"    Completeness:      {r.extraction_completeness:.3f}")
        print(f"    Hallucination Risk:{r.hallucination_risk:.3f}")
        print(f"    Content Match:     {r.content_type_match:.3f}")
        print(f"    OVERALL:           {r.overall:.3f}")
    if response.token_usage:
        t = response.token_usage
        print(f"\n  Token Usage:")
        print(f"    Input:  {t.get('total_input_tokens', 0)}")
        print(f"    Output: {t.get('total_output_tokens', 0)}")
        print(f"    Cost:   ${t.get('estimated_cost_usd', 0):.4f}")

    print(f"\nMechanics:")
    for m in response.mechanics: print(f"  - {m.name} ({m.mechanic_type.value}) [{m.confidence.value}]")

    print(f"\nEvents:")
    for e in response.events[:10]:
        print(f"\n  [{e.section}] {e.description[:100]}")
        if e.dynamics: print(f"    Dynamics: {', '.join(d.value for d in e.dynamics)}")
        if e.player_actions: print(f"    Actions: {', '.join(e.player_actions[:3])}")
        if e.failure_states: print(f"    Failures: {', '.join(e.failure_states[:2])}")
        if e.reliability: print(f"    Reliability: {e.reliability.overall:.3f}")

    print(f"\nWorking Memory Entry:")
    print(json.dumps(response.to_working_memory_entry(), indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="Gameplay Event Agent v2")
    sub = parser.add_subparsers(dest="command")

    p_demo = sub.add_parser("demo", help="Run demo")
    p_demo.add_argument("--mode", choices=["simple", "complex"], default="simple",
                       help="simple (~300 words, ~$0.01) or complex (~600 words, ~$0.02)")

    sub.add_parser("test-edge", help="Test edge cases (no API calls)")
    sub.add_parser("test-full", help="Full integration test (uses API credits, ~$0.05)")

    p_q = sub.add_parser("query", help="Query a game")
    p_q.add_argument("query"); p_q.add_argument("--game", required=True)
    p_q.add_argument("--genre", default="action"); p_q.add_argument("--fandom-wiki", default="")

    args = parser.parse_args()
    if args.command == "demo": cmd_demo(args)
    elif args.command == "test-edge": cmd_test_edge_cases(args)
    elif args.command == "test-full": cmd_test_full(args)
    elif args.command == "query": cmd_query(args)
    else: parser.print_help()

if __name__ == "__main__": main()
