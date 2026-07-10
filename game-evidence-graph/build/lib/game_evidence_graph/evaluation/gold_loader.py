from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def load_gold_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text())


def load_gold_csv(path: str | Path) -> pd.DataFrame:
    return pd.read_csv(path)
