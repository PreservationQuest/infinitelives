# Game Evidence Graph

This repository adapts ReCITE-style long-document causal graph prompting and evaluation to empirical game studies, but represents literature-derived causal claims and intervention evidence rather than independently estimating causal effects.

The project builds an auditable evidence graph from empirical game-study PDFs. It preserves paper, study, intervention, condition, outcome, measurement, quote, page, attribution, and review metadata for every evidence-bearing row and edge.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
game-evidence init
game-evidence run-all --pdf-dir data/input/papers --out data/processed
pytest
```

## Scientific Framing

This is a literature-derived causal claim / intervention evidence graph. It does not build a structural causal model, estimate independent mechanic effects, perform do-calculus, or guarantee outcome changes from a mechanic.

Use outputs as evidence-aware design support:

> This mechanic or mechanic set has prior literature support for association with an outcome under specific study conditions.

## Required Outputs

`game-evidence run-all` writes study ontology, game ontology, Dataset C CSV/JSONL, graph JSON/GraphML, edge table, completeness report, audit report, and review queue files under `data/processed/`.
