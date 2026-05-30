"""SQLite storage for OHLCV price data."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

DEFAULT_DB = Path(__file__).parent.parent / "data" / "prices.db"


def get_conn(db_path: Path = DEFAULT_DB) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS prices (
            ticker  TEXT NOT NULL,
            date    TEXT NOT NULL,
            open    REAL,
            high    REAL,
            low     REAL,
            close   REAL,
            volume  INTEGER,
            PRIMARY KEY (ticker, date)
        );
        CREATE INDEX IF NOT EXISTS idx_prices_ticker ON prices (ticker);
    """)
    conn.commit()


def upsert(
    conn: sqlite3.Connection,
    ticker: str,
    df: pd.DataFrame,
) -> int:
    """Insert or replace rows. Returns count of rows written."""
    rows = [
        (
            ticker.upper(),
            str(row.Index.date()),
            row.Open,
            row.High,
            row.Low,
            row.Close,
            int(row.Volume),
        )
        for row in df.itertuples()
    ]
    conn.executemany(
        "INSERT OR REPLACE INTO prices (ticker, date, open, high, low, close, volume) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    return len(rows)


def query(
    conn: sqlite3.Connection,
    ticker: str,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 100,
) -> pd.DataFrame:
    """Return stored rows as DataFrame. Dates are ISO strings (YYYY-MM-DD)."""
    sql = "SELECT date, open, high, low, close, volume FROM prices WHERE ticker = ?"
    params: list = [ticker.upper()]
    if start:
        sql += " AND date >= ?"
        params.append(start)
    if end:
        sql += " AND date <= ?"
        params.append(end)
    sql += " ORDER BY date DESC LIMIT ?"
    params.append(limit)
    df = pd.read_sql_query(sql, conn, params=params, index_col="date")
    return df


def list_tickers(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT DISTINCT ticker, COUNT(*) AS rows, MIN(date) AS first, MAX(date) AS last "
        "FROM prices GROUP BY ticker ORDER BY ticker"
    ).fetchall()
    return rows
