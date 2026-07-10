from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

import pandas as pd


TITLE_PATTERNS = [
    "www.",
    "journal homepage",
    "contents lists available",
    "open access article under",
    "under the license",
    "page 1 of",
    "vol.:(",
    "procedia -",
    "springerlink",
    "article history",
    "peer-review under responsibility",
]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def _source_pdf_by_paper(study_payload: dict) -> dict[str, str | None]:
    return {
        str(paper.get("paper_id")): paper.get("source_pdf")
        for paper in study_payload.get("papers", [])
        if paper.get("paper_id")
    }


def _paper_titles(study_payload: dict, df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    source_pdf = _source_pdf_by_paper(study_payload)
    for paper in study_payload.get("papers", []):
        rows.append(
            {
                "paper_id": paper.get("paper_id"),
                "paper_title": paper.get("title") or paper.get("paper_title"),
                "source_pdf": paper.get("source_pdf"),
                "year": paper.get("year"),
                "doi": paper.get("doi"),
            }
        )
    if not rows and {"paper_id", "paper_title"}.issubset(df.columns):
        title_df = df[["paper_id", "paper_title", "year", "doi"]].drop_duplicates()
        title_df["source_pdf"] = title_df["paper_id"].map(source_pdf)
        return title_df[["paper_id", "paper_title", "source_pdf", "year", "doi"]]
    return pd.DataFrame(rows)


def _title_reasons(title: object, source_pdf: object = None) -> str:
    text = str(title or "")
    lowered = text.lower()
    reasons: list[str] = []
    if source_pdf and text == str(source_pdf).removesuffix(".pdf"):
        reasons.append("title_is_pdf_stem")
    if re.fullmatch(r"(1-s2\.0-[A-Za-z0-9]+-main|S\d+)", text):
        reasons.append("title_is_file_identifier")
    for pattern in TITLE_PATTERNS:
        if pattern in lowered:
            reasons.append(f"contains:{pattern}")
    if len(text.split()) <= 2:
        reasons.append("very_short_title")
    if len(text) > 240:
        reasons.append("very_long_title")
    return "|".join(reasons)


def build_title_quality_flags(study_payload: dict, df: pd.DataFrame) -> pd.DataFrame:
    titles = _paper_titles(study_payload, df)
    if titles.empty:
        return pd.DataFrame(
            columns=[
                "item_type",
                "item_id",
                "paper_id",
                "field",
                "old_value",
                "source_pdf",
                "reason",
                "new_value",
                "decision",
                "notes",
            ]
        )
    titles["reason"] = titles.apply(
        lambda row: _title_reasons(row.get("paper_title"), row.get("source_pdf")),
        axis=1,
    )
    flagged = titles[titles["reason"].astype(bool)].copy()
    flagged["item_type"] = "title"
    flagged["item_id"] = flagged["paper_id"]
    flagged["field"] = "paper_title"
    flagged["old_value"] = flagged["paper_title"]
    flagged["new_value"] = ""
    flagged["decision"] = ""
    flagged["notes"] = ""
    return flagged[
        [
            "item_type",
            "item_id",
            "paper_id",
            "field",
            "old_value",
            "source_pdf",
            "reason",
            "new_value",
            "decision",
            "notes",
        ]
    ]


def _top_values(values: Iterable[object], limit: int = 5) -> str:
    clean = [str(value) for value in values if pd.notna(value) and str(value)]
    return " | ".join(clean[:limit])


def build_entity_review(
    df: pd.DataFrame,
    field: str,
    item_type: str,
    *,
    include_null: bool = False,
) -> pd.DataFrame:
    if field not in df.columns:
        return pd.DataFrame()
    data = df.copy()
    if not include_null:
        data = data[data[field].notna()]
    if data.empty:
        return pd.DataFrame()
    rows = []
    for value, group in data.groupby(field, dropna=include_null):
        rows.append(
            {
                "item_type": item_type,
                "item_id": str(value),
                "field": field,
                "old_value": value,
                "row_count": len(group),
                "paper_count": group["paper_id"].nunique() if "paper_id" in group else None,
                "supported_count": int(group["is_supported_evidence"].astype(bool).sum())
                if "is_supported_evidence" in group
                else None,
                "example_papers": _top_values(group.get("paper_id", pd.Series()).drop_duplicates()),
                "example_titles": _top_values(group.get("paper_title", pd.Series()).drop_duplicates(), 3),
                "new_value": "",
                "decision": "",
                "notes": "",
            }
        )
    return pd.DataFrame(rows).sort_values(["paper_count", "row_count"], ascending=False)


def build_manual_audit_sample(df: pd.DataFrame, sample_size: int) -> pd.DataFrame:
    if df.empty:
        return df
    pieces: list[pd.DataFrame] = []
    indexed = df.reset_index(names="row_index")
    supported = indexed[indexed["is_supported_evidence"].astype(bool)]
    needs_review = indexed[indexed["review_status"].eq("needs_review")]
    null_games = indexed[indexed["game_id"].isna()] if "game_id" in indexed else indexed.head(0)
    high_weight = supported.sort_values("edge_weight", ascending=False).head(sample_size)
    for label, data in [
        ("supported_random", supported),
        ("needs_review_random", needs_review),
        ("null_game_random", null_games),
        ("high_weight", high_weight),
    ]:
        if data.empty:
            continue
        if label == "high_weight":
            sample = data.copy()
        else:
            sample = data.sample(min(sample_size, len(data)), random_state=7)
        sample = sample.copy()
        sample["audit_bucket"] = label
        pieces.append(sample)
    if not pieces:
        return indexed.head(0)
    sample = pd.concat(pieces, ignore_index=True).drop_duplicates(subset=["row_index"])
    review_cols = [
        "audit_bucket",
        "row_index",
        "paper_id",
        "paper_title",
        "game_id",
        "game_name",
        "mechanic_id",
        "mechanic_name",
        "outcome_canonical",
        "outcome_category",
        "effect_direction",
        "effect_size_raw",
        "p_value",
        "source_quote",
        "is_supported_evidence",
        "edge_weight",
        "review_status",
    ]
    existing = [col for col in review_cols if col in sample.columns]
    sample = sample[existing].sort_values(["audit_bucket", "paper_id", "row_index"])
    sample["decision"] = ""
    sample["notes"] = ""
    return sample


def ensure_audit_decisions_template(path: Path) -> None:
    if path.exists():
        return
    columns = [
        "item_type",
        "item_id",
        "field",
        "old_value",
        "new_value",
        "decision",
        "notes",
    ]
    pd.DataFrame(columns=columns).to_csv(path, index=False)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create non-destructive audit CSVs from processed outputs.")
    parser.add_argument("--processed", type=Path, default=Path("data/processed"))
    parser.add_argument("--out", type=Path, default=Path("data/audit"))
    parser.add_argument("--sample-size", type=int, default=50)
    args = parser.parse_args()

    processed = args.processed
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(processed / "mechanic_intervention_dataset.csv")
    study_payload = _read_json(processed / "study_ontology.json")

    title_flags = build_title_quality_flags(study_payload, df)
    game_review = build_entity_review(df, "game_name", "game")
    mechanic_review = build_entity_review(df, "mechanic_name", "mechanic")
    outcome_category_review = build_entity_review(df, "outcome_category", "outcome_category")
    manual_sample = build_manual_audit_sample(df, args.sample_size)

    write_csv(title_flags, out / "title_quality_flags.csv")
    write_csv(game_review, out / "game_entity_review.csv")
    write_csv(mechanic_review, out / "mechanic_review.csv")
    write_csv(outcome_category_review, out / "outcome_category_review.csv")
    write_csv(manual_sample, out / "manual_audit_sample.csv")
    ensure_audit_decisions_template(out / "audit_decisions.csv")

    summary = pd.DataFrame(
        [
            {"file": "title_quality_flags.csv", "rows": len(title_flags)},
            {"file": "game_entity_review.csv", "rows": len(game_review)},
            {"file": "mechanic_review.csv", "rows": len(mechanic_review)},
            {"file": "outcome_category_review.csv", "rows": len(outcome_category_review)},
            {"file": "manual_audit_sample.csv", "rows": len(manual_sample)},
            {"file": "audit_decisions.csv", "rows": len(pd.read_csv(out / "audit_decisions.csv"))},
        ]
    )
    write_csv(summary, out / "audit_summary.csv")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
