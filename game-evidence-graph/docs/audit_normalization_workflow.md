# Audit and Normalization Workflow

`data/processed/` is treated as the frozen extraction snapshot. The audit and
normalization pass is non-destructive:

- `data/audit/` contains CSVs for human review and decisions.
- `data/normalized/` contains derived outputs after applying normalization maps
  and audit decisions.
- `configs/normalization/` contains reusable mapping files.

## Create Audit Files

```bash
.venv/bin/python scripts/create_audit_samples.py \
  --processed data/processed \
  --out data/audit \
  --sample-size 50
```

This writes:

- `data/audit/title_quality_flags.csv`
- `data/audit/game_entity_review.csv`
- `data/audit/mechanic_review.csv`
- `data/audit/outcome_category_review.csv`
- `data/audit/manual_audit_sample.csv`
- `data/audit/audit_decisions.csv`

Use `audit_decisions.csv` to record manual changes:

```csv
item_type,item_id,field,old_value,new_value,decision,notes
title,paper_084,paper_title,"old title","Corrected title",edit,"PDF title extraction issue"
row,1234,game_name,"action video games","",set_null,"Generic genre, not a named game"
outcome_category,Behavioral,outcome_category,"behavioral","Behavioral",canonicalize,"case cleanup"
```

Supported `decision` values are:

- `edit`
- `canonicalize`
- `set_null`

## Apply Normalization

```bash
.venv/bin/python scripts/apply_normalization.py \
  --processed data/processed \
  --configs configs/normalization \
  --audit data/audit \
  --out data/normalized
```

This writes a full derived dataset to `data/normalized/` and rebuilds the graph,
reports, and review queue from the normalized Dataset C.

## Mapping Files

- `configs/normalization/outcome_category_map.yaml`
- `configs/normalization/game_name_map.yaml`
- `configs/normalization/mechanic_name_map.yaml`
- `configs/normalization/title_overrides.yaml`

Keep these conservative. Prefer adding mappings only after reviewing the audit
CSVs.
