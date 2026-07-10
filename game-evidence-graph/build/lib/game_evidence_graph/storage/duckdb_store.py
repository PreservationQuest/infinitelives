from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_duckdb_table(path: str | Path, table: str, df: pd.DataFrame) -> None:
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError("Install duckdb to use DuckDB storage.") from exc
    with duckdb.connect(str(path)) as conn:
        conn.sql(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM df")
