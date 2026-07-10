from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

from game_evidence_graph.schemas.review import ReviewItem


def _optional_str(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value)
    return text if text else None


def build_review_queue(df: pd.DataFrame) -> list[ReviewItem]:
    items: list[ReviewItem] = []
    idx = 1
    for _, row in df.iterrows():
        reasons: list[str] = []
        if row.get("review_status") == "needs_review":
            reasons.append("Row marked needs_review.")
        if row.get("attribution_level") in {"ontology_inferred_mechanic", "mechanic_set_inferred"}:
            reasons.append("Mechanic attribution is inferred.")
        if not row.get("source_quote") and row.get("is_supported_evidence"):
            reasons.append("Supported evidence missing source quote.")
        if row.get("attribution_level") == "unsupported_or_overgenerated":
            reasons.append("Unsupported or overgenerated row.")
        if reasons:
            source_quote = _optional_str(row.get("source_quote"))
            items.append(
                ReviewItem(
                    review_id=f"rev_{idx:05d}",
                    item_type="attribution_level",
                    paper_id=_optional_str(row.get("paper_id")),
                    study_id=_optional_str(row.get("study_id")),
                    current_value=str(row.get("attribution_level")),
                    suggested_value=None,
                    reason_for_review=" ".join(reasons),
                    source_quote=source_quote,
                    source_page=int(row["source_page"]) if pd.notna(row.get("source_page")) else None,
                )
            )
            idx += 1
    return items


def write_review_jsonl(items: list[ReviewItem], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(item.model_dump_json() for item in items) + ("\n" if items else ""))


def export_review_csv(jsonl_path: str | Path, csv_path: str | Path) -> None:
    rows = [json.loads(line) for line in Path(jsonl_path).read_text().splitlines() if line.strip()]
    p = Path(csv_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ReviewItem.model_fields.keys())
        writer.writeheader()
        writer.writerows(rows)
