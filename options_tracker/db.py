import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

_DEFAULT_DB = os.getenv("OPTIONS_TRACKER_DB", str(Path.cwd() / "options_tracker.db"))


def get_db_path() -> str:
    return _DEFAULT_DB


@contextmanager
def connect(db_path: Optional[str] = None):
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    try:
        conn.row_factory = sqlite3.Row
        yield conn
    finally:
        conn.commit()
        conn.close()


def init_db(db_path: Optional[str] = None) -> None:
    with connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY,
                datetime TEXT NOT NULL,
                symbol TEXT NOT NULL,
                expiry TEXT NOT NULL,
                strike REAL NOT NULL,
                right TEXT NOT NULL CHECK(right IN ('C','P')),
                action TEXT NOT NULL CHECK(action IN ('BUY','SELL')),
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                commission REAL NOT NULL DEFAULT 0,
                fees REAL NOT NULL DEFAULT 0,
                multiplier INTEGER NOT NULL DEFAULT 100,
                tag TEXT
            );
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_trades_key
            ON trades(symbol, expiry, strike, right, datetime);
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS price_updates (
                id INTEGER PRIMARY KEY,
                symbol TEXT NOT NULL,
                expiry TEXT NOT NULL,
                strike REAL NOT NULL,
                right TEXT NOT NULL CHECK(right IN ('C','P')),
                mark REAL NOT NULL,
                updated_at TEXT NOT NULL
            );
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_marks_key
            ON price_updates(symbol, expiry, strike, right, updated_at);
            """
        )


def insert_trade(trade: Dict, db_path: Optional[str] = None) -> int:
    with connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO trades
            (datetime, symbol, expiry, strike, right, action, quantity, price, commission, fees, multiplier, tag)
            VALUES (:datetime, :symbol, :expiry, :strike, :right, :action, :quantity, :price, :commission, :fees, :multiplier, :tag)
            """,
            trade,
        )
        return cur.lastrowid


def insert_trades(trades: Iterable[Dict], db_path: Optional[str] = None) -> int:
    count = 0
    with connect(db_path) as conn:
        cur = conn.cursor()
        for t in trades:
            cur.execute(
                """
                INSERT INTO trades
                (datetime, symbol, expiry, strike, right, action, quantity, price, commission, fees, multiplier, tag)
                VALUES (:datetime, :symbol, :expiry, :strike, :right, :action, :quantity, :price, :commission, :fees, :multiplier, :tag)
                """,
                t,
            )
            count += 1
    return count


def fetch_trades(db_path: Optional[str] = None) -> List[sqlite3.Row]:
    with connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM trades ORDER BY datetime ASC, id ASC"
        )
        return cur.fetchall()


def fetch_trades_window(dt_from: Optional[str], dt_to: Optional[str], db_path: Optional[str] = None) -> List[sqlite3.Row]:
    query = "SELECT * FROM trades WHERE 1=1"
    params: List = []
    if dt_from:
        query += " AND datetime >= ?"
        params.append(dt_from)
    if dt_to:
        query += " AND datetime <= ?"
        params.append(dt_to)
    query += " ORDER BY datetime ASC, id ASC"

    with connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()


def upsert_mark(symbol: str, expiry: str, strike: float, right: str, mark: float, updated_at: str, db_path: Optional[str] = None) -> None:
    with connect(db_path) as conn:
        cur = conn.cursor()
        # Store as an append-only table; newest updated_at is used by readers
        cur.execute(
            """
            INSERT INTO price_updates(symbol, expiry, strike, right, mark, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (symbol, expiry, strike, right, mark, updated_at),
        )


def get_latest_mark(symbol: str, expiry: str, strike: float, right: str, db_path: Optional[str] = None) -> Optional[Tuple[float, str]]:
    with connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT mark, updated_at
            FROM price_updates
            WHERE symbol = ? AND expiry = ? AND strike = ? AND right = ?
            ORDER BY updated_at DESC, id DESC
            LIMIT 1
            """,
            (symbol, expiry, strike, right),
        )
        row = cur.fetchone()
        if not row:
            return None
        return float(row[0]), str(row[1])