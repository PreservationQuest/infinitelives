# Scientific Limitations

This system constructs a literature-derived causal claim / intervention evidence graph.

It does not independently estimate causal effects.

Mechanic-level edges often come from ontology-inferred attribution.

Individual mechanics should not be interpreted as isolated causes unless `attribution_level` is `paper_explicit_mechanic`.

Evidence-aware design queries are design-support recommendations, not do-calculus counterfactual estimates.

The strongest supported edge type is `INTERVENTION_REPORTED_EFFECT_ON_OUTCOME`, meaning a paper reports that an intervention condition affected, predicted, differed on, or was associated with an outcome measure.
