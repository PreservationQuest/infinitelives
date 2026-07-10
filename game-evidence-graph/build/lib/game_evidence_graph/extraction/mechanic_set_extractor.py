from __future__ import annotations

from game_evidence_graph.schemas.game import GameOntology
from game_evidence_graph.schemas.mechanic import MechanicSet
from game_evidence_graph.schemas.study import StudyOntology


def derive_mechanic_sets(studies: StudyOntology, games: GameOntology) -> list[MechanicSet]:
    games_by_id = {game.game_id: game for game in games.games}
    sets: list[MechanicSet] = []
    idx = 1
    for study in studies.studies:
        for intervention in study.interventions:
            for condition in intervention.conditions:
                mechanics: list[str] = []
                for game_id in condition.game_ids:
                    game = games_by_id.get(game_id)
                    if game:
                        mechanics.extend([m.mechanic_name for m in game.mechanics if m.mechanic_name])
                if mechanics:
                    sets.append(
                        MechanicSet(
                            mechanic_set_id=f"ms_{idx:04d}",
                            mechanics=sorted(set(mechanics)),
                            game_ids=condition.game_ids,
                            attribution_level="mechanic_set_inferred",
                            confidence=0.6,
                        )
                    )
                    idx += 1
    return sets
