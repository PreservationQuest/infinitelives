# Schema

Every evidence-bearing row and edge includes:

- `paper_id`
- `study_id`
- `intervention_id`
- `condition_id`
- `outcome_id`
- `measurement_id`
- `source_quote`
- `source_page`
- `evidence_strength`
- `attribution_level`
- `claim_type`
- `claim_explicitness`
- `extraction_confidence`
- `review_status`

Mechanic-level rows must include `attribution_level`. Blank-effect rows are marked `unsupported_or_overgenerated`, `is_supported_evidence = false`, and `edge_weight = 0`.

## Conditions

`interventions[].conditions` means study arms or comparison groups, such as treatment, control, exposure, or comparison conditions.

Domain-level conditions are represented separately:

- `research_categories`: controlled paper/study categories such as Addiction, Education, Neuro/Cognitive, Physiological, Psychological, or Social.
- `studied_conditions`: the phenomenon, diagnosis, topic condition, or context of interest, such as multiple sclerosis, addiction, postural balance, empathy, motivation, or sexualization.

## Game Ontology Seeds

Seed game ontology files may use either the internal schema or a simpler JSON format with:

- `game_id`
- `game_name`
- `developer`
- `publisher`
- `release_year`
- `genre`
- `platform`
- `mechanics`
- `dynamics`
- `aesthetics`
- `core_gameplay_loop`
- `gameplay_objective`
- `player_perspective`
- `multiplayer_type`
- `progression_system`
- `npc_interaction`
- `procedural_generation`
- `world_persistence`
- `skill_requirement`
- `cognitive_demands`
- `social_features`
- `communication_requirement`
- `gameplay_summary`
- `confidence`

When seeds use string lists for `mechanics`, `dynamics`, or `aesthetics`, the loader converts them to feature records. `game_name` is accepted as an alias for `canonical_game_name`. String confidence values such as `High`, `Medium`, or `Low` are retained in `confidence_label` and mapped to numeric `confidence`.
