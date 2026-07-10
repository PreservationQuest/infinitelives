from __future__ import annotations

from game_evidence_graph.schemas.game import GameOntology, GameRecord, OntologyFeature
from game_evidence_graph.schemas.study import (
    Condition,
    Intervention,
    Outcome,
    Population,
    StudyOntology,
    StudyRecord,
)


def sample_study(effect: bool = True, mechanic_name: str = "Puzzle Solving") -> tuple[StudyOntology, GameOntology]:
    outcome = Outcome(
        outcome_id="out_001",
        outcome_raw="concept-map performance",
        outcome_canonical="concept_map_performance",
        outcome_category="learning",
        measurement_id="meas_001",
        measurement_raw="concept map score",
        measurement_type="concept_map",
        effect_direction="positive" if effect else "not_reported",
        effect_size_raw="The game group outperformed lecture review." if effect else None,
        p_value="p < .05" if effect else None,
        effect_target_measure="concept map score",
        source_quote="The game group outperformed lecture review." if effect else None,
        source_page=8 if effect else None,
        page_trace_status="found" if effect else "not_found",
    )
    study = StudyRecord(
        paper_id="paper_001",
        paper_title="Physics Game Study",
        year=2024,
        study_id="paper_001_study_01",
        population=Population(population_id="pop_001", population_raw="ninth-grade students", sample_size=60),
        study_design="quasi_experimental",
        evidence_strength="quasi_experimental",
        context="classroom",
        intervention_duration="two weeks",
        extraction_confidence=0.8,
        review_status="auto_extracted",
        interventions=[
            Intervention(
                intervention_id="paper_001_study_01_int_01",
                treatment_raw="game-based physics review",
                control_raw="lecture-based review",
                conditions=[
                    Condition(
                        condition_id="paper_001_study_01_cond_treatment",
                        condition_type="treatment",
                        game_mentions=["Cut the Rope"],
                        game_ids=["g01"],
                    )
                ],
            )
        ],
        outcomes=[outcome],
    )
    game = GameRecord(
        game_id="g01",
        canonical_game_name="Cut the Rope",
        game_match_confidence="high",
        confidence=0.8,
        review_status="auto_extracted",
        mechanics=[
            OntologyFeature(mechanic_id="m001", mechanic_name=mechanic_name, source="paper_text", confidence=0.8),
            OntologyFeature(mechanic_id="m002", mechanic_name="Physics Interaction", source="paper_text", confidence=0.8),
        ],
    )
    return StudyOntology(studies=[study]), GameOntology(games=[game])
