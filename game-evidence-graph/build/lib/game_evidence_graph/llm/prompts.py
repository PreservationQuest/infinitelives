GENERAL_RULES = """
- Do not invent information.
- If a field is not reported, return null or not_reported.
- Preserve exact source quotes.
- Include source page numbers when possible.
- Separate treatment from control.
- Use interventions.conditions only for study arms such as treatment, control, comparison, or exposure groups.
- Extract paper-level research_categories from this controlled list: Addiction, Behavioral, Economics, Education, Environmental, Ethical, Governance, Learning, Neuro/Cognitive, Physiological, Policy-making, Psychological, Sexualization, Social, Technological.
- Extract studied_conditions for the domain condition or phenomenon of interest, such as multiple sclerosis, addiction, postural balance context, empathy, motivation, climate behavior, governance, sexualization, or learning.
- Separate measured outcomes from interpreted constructs.
- Separate game-level claims from mechanic-level claims.
- Separate mechanics from events.
- Do not create mechanic-outcome links without attribution_level.
- Be conservative.
- Output strict JSON only.
- Do not output chain-of-thought.
""".strip()


STUDY_ONTOLOGY_PROMPT = (
    "You extract empirical game study ontology records from page-numbered paper text.\n"
    f"{GENERAL_RULES}\n"
    "Return strict JSON with this shape:\n"
    "{\n"
    '  "paper_id": "...",\n'
    '  "paper_title": "...",\n'
    '  "studies": [\n'
    "    {\n"
    '      "study_id": "...",\n'
    '      "study_label": "...",\n'
    '      "research_categories": ["Addiction|Behavioral|Economics|Education|Environmental|Ethical|Governance|Learning|Neuro/Cognitive|Physiological|Policy-making|Psychological|Sexualization|Social|Technological"],\n'
    '      "studied_conditions": ["domain condition or phenomenon such as multiple sclerosis, empathy, addiction, postural balance"],\n'
    '      "population": {"population_raw": "...", "sample_size": null, "studied_conditions": []},\n'
    '      "study_design": "randomized_controlled_trial|quasi_experimental|case_control|within_subject_experimental|within_subject_observational|between_subject_observational|correlational|pre_post_no_control|qualitative|mixed_methods|not_reported|unclear",\n'
    '      "evidence_strength": "same controlled vocabulary as study_design",\n'
    '      "context": "...",\n'
    '      "intervention_duration": "...",\n'
    '      "interventions": [\n'
    "        {\n"
    '          "intervention_name": "...",\n'
    '          "treatment_raw": "...",\n'
    '          "control_raw": "...",\n'
    '          "conditions": [\n'
    '            {"condition_type": "treatment|control|comparison|exposure|unclear", "description": "...", "game_mentions": ["named game or platform, e.g. Minecraft, Nintendo Wii, Wii Fit, Xbox Kinect"]}\n'
    "          ]\n"
    "        }\n"
    "      ],\n"
    '      "outcomes": [\n'
    "        {\n"
    '          "outcome_raw": "measured outcome, not population/topic condition",\n'
    '          "outcome_canonical": "...",\n'
    '          "outcome_category": "...",\n'
    '          "measurement_raw": "instrument, scale, test, or measure",\n'
    '          "measurement_type": "...",\n'
    '          "effect_direction": "positive|negative|null|mixed|not_reported|unclear",\n'
    '          "effect_size_raw": "...",\n'
    '          "p_value": "...",\n'
    '          "confidence_interval": "...",\n'
    '          "source_quote": "exact quote supporting this outcome/effect",\n'
    '          "source_page": 1\n'
    "        }\n"
    "      ],\n"
    '      "extraction_confidence": 0.0,\n'
    '      "review_status": "needs_review"\n'
    "    }\n"
    "  ]\n"
    "}\n"
    "Important: postural balance, empathy, motivation, aggression, learning, gaming disorder, and cognitive performance are outcomes or studied conditions, not treatment/control arms. Treatment/control arms belong only in interventions.conditions."
)
GAME_ONTOLOGY_PROMPT = (
    "You extract named or described games and game ontology features from empirical game papers.\n"
    f"{GENERAL_RULES}\nReturn JSON with games."
)
MECHANIC_SET_PROMPT = (
    "Derive mechanic sets tied to specific paper/study/intervention/condition records.\n"
    f"{GENERAL_RULES}\nReturn JSON with mechanic_sets."
)
DATASET_C_PROMPT = (
    "Generate mechanic intervention dataset rows without overclaiming isolated mechanic effects.\n"
    f"{GENERAL_RULES}\nReturn JSON with mechanic_intervention_rows."
)
CAUSAL_CLAIM_EDGE_PROMPT = (
    "Extract literature-derived causal claim and intervention-evidence graph edges for empirical game studies.\n"
    "Use ReCITE-style strict relationship output, but include rich evidence-bearing fields.\n"
    f"{GENERAL_RULES}\nReturn JSON with causal_claim_edges."
)
