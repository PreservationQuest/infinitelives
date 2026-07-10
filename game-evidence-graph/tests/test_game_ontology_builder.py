from pathlib import Path

from game_evidence_graph.datasets.game_ontology_builder import infer_game_mentions_from_text, infer_mechanics, load_seed_game_ontology


def test_infer_exergame_mechanics():
    names = [feature.mechanic_name for feature in infer_mechanics("Nintendo Wii Fit")]
    assert "Balance Training" in names
    assert "Gesture Input" in names


def test_infer_minecraft_mechanics():
    names = [feature.mechanic_name for feature in infer_mechanics("Minecraft")]
    assert "Cooperative Play" in names
    assert "Building" in names


def test_infer_game_mentions_from_intervention_text():
    assert infer_game_mentions_from_text("Virtual cooperative multiplayer Minecraft intervention") == ["Minecraft"]
    assert infer_game_mentions_from_text("Participants used an active video game") == []


def test_seed_game_ontology_accepts_example_shape():
    path = Path("data/input/seed_game_ontology.json")
    ontology = load_seed_game_ontology(path)
    assert len(ontology.games) == 4
    counter_strike = ontology.games[0]
    assert counter_strike.game_id == "GAME_0001"
    assert counter_strike.game_name == "Counter-Strike"
    assert counter_strike.canonical_game_name == "Counter-Strike"
    assert counter_strike.confidence_label == "High"
    assert counter_strike.confidence == 0.9
    assert counter_strike.mechanics[0].mechanic_name == "Combat"
    assert counter_strike.dynamics[0].dynamic_name == "Team Coordination"
    assert counter_strike.aesthetics[0].aesthetic_name == "Challenge"
