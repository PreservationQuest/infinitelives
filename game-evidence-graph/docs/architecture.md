# Architecture

The repository is organized as layered services:

- `ingestion`: PDF-to-page text extraction with page traceability.
- `llm`: abstract clients, mock client, prompts, JSON repair.
- `schemas`: Pydantic records for papers, studies, games, evidence, graph edges, queries, and review.
- `datasets`: ontology builders, Dataset C builder, validators, exporters, completeness reports.
- `graph`: NetworkX-compatible evidence graph construction and export.
- `query`: evidence-aware design query ranking and explanations.
- `evaluation`: graph and extraction metrics plus LLM judge prompts.
- `recite_adapter`: optional ReCITE/ReVITE inspection and adaptation documentation.

All LLM calls go through `LLMClient`; tests use `MockLLMClient`.
