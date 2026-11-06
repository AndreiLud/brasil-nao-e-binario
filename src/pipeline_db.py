"""DuckDB helpers: open the project database and run the SQL files in order."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import duckdb

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import config as C


def connect(fresh: bool = False) -> duckdb.DuckDBPyConnection:
    C.INTERIM.mkdir(parents=True, exist_ok=True)
    if fresh and C.DB_PATH.exists():
        C.DB_PATH.unlink()
    os.chdir(C.ROOT)  # SQL files use paths relative to the project root
    con = duckdb.connect(str(C.DB_PATH))
    con.execute("SET threads TO 4")
    return con


def run_sql(con: duckdb.DuckDBPyConnection, name: str):
    con.execute((C.SQL_DIR / name).read_text(encoding="utf-8"))


def load_reference(con: duckdb.DuckDBPyConnection):
    con.execute("CREATE OR REPLACE TABLE municipalities AS SELECT * FROM read_parquet('data/interim/municipalities.parquet')")
