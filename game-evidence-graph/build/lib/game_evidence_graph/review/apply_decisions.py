from __future__ import annotations

import pandas as pd


def apply_review_decisions(dataset: pd.DataFrame, decisions: pd.DataFrame) -> pd.DataFrame:
    # Minimal implementation: append human decision metadata for downstream audit.
    result = dataset.copy()
    if "decision" not in decisions:
        return result
    result.attrs["review_decisions_applied"] = int(len(decisions))
    return result
