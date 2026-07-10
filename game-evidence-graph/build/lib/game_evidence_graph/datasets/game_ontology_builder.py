from __future__ import annotations

import json
from pathlib import Path

from game_evidence_graph.canonicalization.ids import next_game_id
from game_evidence_graph.schemas.game import GameOntology, GameRecord, OntologyFeature
from game_evidence_graph.schemas.study import StudyOntology

MECHANIC_IDS = {
    "Combat": "m001",
    "Movement Control": "m002",
    "Balance Training": "m003",
    "Gesture Input": "m004",
    "Physical Imitation": "m005",
    "Cooperative Play": "m006",
    "Perspective Taking": "m007",
    "Building": "m008",
    "Exploration": "m009",
    "Rapid Response": "m010",
    "Targeting": "m011",
    "Driving": "m012",
    "Sports Simulation": "m013",
    "Immersive Interaction": "m014",
    "Multisensory Feedback": "m015",
    "Puzzle Solving": "m016",
}


def infer_mechanics(game_name: str) -> list[OntologyFeature]:
    name = game_name.lower()
    mechanics: list[str] = []
    if any(term in name for term in ["wii fit", "exergame", "active video game", "fitness", "your shape"]):
        mechanics.extend(["Movement Control", "Balance Training", "Gesture Input", "Physical Imitation"])
    if any(term in name for term in ["kinect", "xbox 360", "wii sport", "sports", "tennis", "bowling", "boxing"]):
        mechanics.extend(["Gesture Input", "Sports Simulation", "Movement Control"])
    if any(term in name for term in ["minecraft"]):
        mechanics.extend(["Cooperative Play", "Building", "Exploration", "Perspective Taking"])
    if any(term in name for term in ["action video", "first-person shooter", "fps", "counter-strike"]):
        mechanics.extend(["Combat", "Rapid Response", "Targeting", "Movement Control"])
    if any(term in name for term in ["driving", "ride"]):
        mechanics.extend(["Driving", "Movement Control"])
    if any(term in name for term in ["virtual reality", "vr"]):
        mechanics.extend(["Immersive Interaction", "Multisensory Feedback", "Movement Control"])
    if any(term in name for term in ["puzzle", "angry birds", "cut the rope"]):
        mechanics.extend(["Puzzle Solving", "Targeting"])

    seen: set[str] = set()
    features: list[OntologyFeature] = []
    for mechanic in mechanics:
        if mechanic in seen:
            continue
        seen.add(mechanic)
        features.append(
            OntologyFeature(
                mechanic_id=MECHANIC_IDS.get(mechanic, f"m{len(MECHANIC_IDS) + 1:03d}"),
                mechanic_name=mechanic,
                source="ontology_inferred",
                confidence=0.45,
            )
        )
    return features


def infer_game_mentions_from_text(text: str) -> list[str]:
    lowered = text.lower()
    mentions: list[str] = []
    known = [
        "Minecraft",
        "Nintendo Wii",
        "Wii Fit Plus",
        "Wii Fit",
        "Wii Sport bowling",
        "Wii boxing",
        "Wii tennis",
        "Xbox 360 Kinect",
        "Xbox 360",
        "Kinect Sports",
        "Kinect Joy Ride",
        "Kinect Adventures",
        "Your Shape Fitness Evolved",
        "World of Warcraft",
        "Counter-Strike",
        "League of Legends",
        "Angry Birds",
        "Cut the Rope",
    ]
    for name in known:
        if name.lower() in lowered and name not in mentions:
            mentions.append(name)
    return mentions


def load_seed_game_ontology(path: str | Path | None) -> GameOntology:
    if not path or not Path(path).exists():
        return GameOntology()
    data = json.loads(Path(path).read_text())
    if isinstance(data, list):
        data = {"games": data}
    return GameOntology.model_validate(data)


def build_game_ontology(studies: StudyOntology, seed_path: str | Path | None = None) -> GameOntology:
    ontology = load_seed_game_ontology(seed_path)
    existing_names = {game.canonical_game_name.lower(): game for game in ontology.games}
    for study in studies.studies:
        for intervention in study.interventions:
            for condition in intervention.conditions:
                if not condition.game_mentions:
                    text = " ".join(
                        value or ""
                        for value in [
                            study.paper_title,
                            intervention.intervention_name,
                            intervention.treatment_raw,
                            intervention.control_raw,
                            condition.description,
                        ]
                    )
                    condition.game_mentions = infer_game_mentions_from_text(text)
                for mention in condition.game_mentions:
                    if mention.lower() in existing_names:
                        game = existing_names[mention.lower()]
                    else:
                        game = GameRecord(
                            game_id=next_game_id([g.game_id for g in ontology.games]),
                            canonical_game_name=mention,
                            mechanics=infer_mechanics(mention),
                            source_papers=[study.paper_id],
                            confidence=0.45,
                            game_match_confidence="needs_review",
                            review_status="needs_review",
                        )
                        ontology.games.append(game)
                        existing_names[mention.lower()] = game
                    if game.game_id not in condition.game_ids:
                        condition.game_ids.append(game.game_id)
                    if study.paper_id not in game.source_papers:
                        game.source_papers.append(study.paper_id)
    return ontology
