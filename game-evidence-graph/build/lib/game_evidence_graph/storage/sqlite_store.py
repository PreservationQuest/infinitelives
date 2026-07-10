from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def write_sqlite_table(path: str | Path, table: str, df: pd.DataFrame) -> None:
    with sqlite3.connect(path) as conn:
        df.to_sql(table, conn, if_exists="replace", index=False)
