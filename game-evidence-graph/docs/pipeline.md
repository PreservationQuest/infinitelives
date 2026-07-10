# Pipeline

1. `game-evidence ingest` extracts page-level text from PDFs.
2. `game-evidence extract-studies` creates normalized study records.
3. `game-evidence build-game-ontology` builds or updates game ontology records.
4. `game-evidence build-mechanic-interventions` derives Dataset C rows.
5. `game-evidence build-graph` exports graph JSON, GraphML, and edge tables.
6. `game-evidence report` creates completeness and audit reports.

`game-evidence run-all` runs the local batch pipeline with the mock LLM client by default.
