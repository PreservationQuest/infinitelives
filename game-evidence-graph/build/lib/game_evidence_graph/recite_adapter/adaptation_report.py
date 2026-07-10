from __future__ import annotations

from pathlib import Path

from game_evidence_graph.recite_adapter.inspect_repo import inspect_repo


def build_adaptation_report(repo_path: str | Path) -> str:
    info = inspect_repo(repo_path)
    modules = "\n".join(f"- {m}" for m in info["python_modules"][:50]) or "- None found"
    prompts = "\n".join(f"- {p}" for p in info["prompt_files"][:30]) or "- None found"
    return f"""# ReCITE Adaptation Report

## ReCITE Repo Structure

Inspected repository: `{info["repo_path"]}`

Commit inspected: `{info["commit"]}`

Representative modules:
{modules}

Representative prompt files:
{prompts}

## Relevant Modules

The reference code is useful for conservative JSON parsing, prompt templates that require grounded evidence quotes, batch LLM orchestration, validation checks, and benchmark-style graph/evidence evaluation.

## Reusable Prompt Patterns

- Require strict JSON only.
- Ask for concise evidence quotes rather than hidden reasoning.
- Prefer conservative labels when source support is weak.
- Return null, unclear, or not_reported rather than inventing values.

## Reusable Metric Ideas

- Node precision and recall.
- Edge precision, recall, F1, and structural Hamming distance.
- LLM-as-judge evaluation one dimension at a time.
- Source-text support and explicitness labeling.

## Assumptions Not Reused

- Economist or business-reputation persona assumptions.
- Simple source/sink-only causal relationships.
- Any assumption that long documents contain a complete ground-truth causal graph.
- Any claim that ontology-inferred mechanics are independently tested causes.

## How This Project Differs

This project constructs a literature-derived causal claim and intervention evidence graph for empirical game studies. It represents reported intervention effects, associations, mechanism hypotheses, and mechanic-set attribution with traceability to papers, studies, conditions, outcomes, measurements, source quotes, source pages, and human review status.

## License And Attribution Notes

No reference modules are imported as required runtime dependencies. If ReCITE/ReVITE code is imported later, it should remain optional, documented in `docs/third_party.md`, and used only where license terms permit.
"""


def write_adaptation_report(repo_path: str | Path, out_path: str | Path) -> None:
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(build_adaptation_report(repo_path))
