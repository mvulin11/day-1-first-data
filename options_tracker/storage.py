import os
from typing import Optional
import pandas as pd
from dateutil import parser

TRADES_CSV_PATH = os.environ.get("OPTIONS_TRADES_CSV", "/workspace/options_tracker/trades.csv")

TRADE_COLUMNS = [
    "id",
    "group_id",
    "symbol",
    "expiry",
    "strike",
    "option_type",
    "action",
    "quantity",
    "price",
    "fees",
    "trade_datetime",
    "note",
]

ACTION_VALUES = {"BTO", "STO", "BTC", "STC"}
OPTION_TYPES = {"C", "P"}


def ensure_storage() -> None:
    os.makedirs(os.path.dirname(TRADES_CSV_PATH), exist_ok=True)
    if not os.path.exists(TRADES_CSV_PATH):
        df = pd.DataFrame(columns=TRADE_COLUMNS)
        df.to_csv(TRADES_CSV_PATH, index=False)


def _coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    # Coerce dtypes
    df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")
    df["group_id"] = pd.to_numeric(df["group_id"], errors="coerce").astype("Int64")
    df["symbol"] = df["symbol"].astype(str)
    # Expiry stored as date string YYYY-MM-DD
    df["expiry"] = pd.to_datetime(df["expiry"], errors="coerce").dt.date
    df["strike"] = pd.to_numeric(df["strike"], errors="coerce")
    df["option_type"] = df["option_type"].astype(str).str.upper()
    df["action"] = df["action"].astype(str).str.upper()
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["fees"] = pd.to_numeric(df["fees"], errors="coerce").fillna(0.0)
    df["trade_datetime"] = pd.to_datetime(df["trade_datetime"], errors="coerce")
    df["note"] = df["note"].astype(str)
    return df


def load_trades() -> pd.DataFrame:
    ensure_storage()
    df = pd.read_csv(TRADES_CSV_PATH)
    df = _coerce_types(df)
    # Ensure sorted by time
    if not df.empty:
        df = df.sort_values("trade_datetime").reset_index(drop=True)
    return df


def save_trades(df: pd.DataFrame) -> None:
    ensure_storage()
    # Keep only known columns in order
    for col in TRADE_COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[TRADE_COLUMNS]
    # Normalize types for saving
    df = df.copy()
    df["expiry"] = pd.to_datetime(df["expiry"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["trade_datetime"] = pd.to_datetime(df["trade_datetime"], errors="coerce").dt.strftime("%Y-%m-%d %H:%M:%S")
    df.to_csv(TRADES_CSV_PATH, index=False)


def next_trade_id(df: Optional[pd.DataFrame] = None) -> int:
    if df is None:
        df = load_trades()
    if df.empty or df["id"].isna().all():
        return 1
    return int(df["id"].max()) + 1


def upsert_trade(row: dict) -> pd.DataFrame:
    df = load_trades()
    # Validate basics
    if row.get("action") not in ACTION_VALUES:
        raise ValueError(f"Invalid action {row.get('action')}")
    if row.get("option_type") not in OPTION_TYPES:
        raise ValueError(f"Invalid option_type {row.get('option_type')}")

    row = row.copy()
    # Parse and normalize
    if isinstance(row.get("expiry"), str):
        row["expiry"] = parser.parse(row["expiry"]).date()
    if isinstance(row.get("trade_datetime"), str):
        row["trade_datetime"] = parser.parse(row["trade_datetime"])    

    if not row.get("id"):
        row["id"] = next_trade_id(df)

    # Convert to DataFrame row
    new_df = pd.DataFrame([{col: row.get(col) for col in TRADE_COLUMNS}])
    # Merge: replace if id exists, else append
    if (df["id"] == row["id"]).any():
        df = df[df["id"] != row["id"]]
    df = pd.concat([df, new_df], ignore_index=True)
    df = _coerce_types(df)
    df = df.sort_values("trade_datetime").reset_index(drop=True)
    save_trades(df)
    return df


def delete_trade(trade_id: int) -> pd.DataFrame:
    df = load_trades()
    df = df[df["id"] != trade_id].reset_index(drop=True)
    save_trades(df)
    return df


def export_trades_csv(path: str) -> None:
    df = load_trades()
    df.to_csv(path, index=False)


def import_trades_csv(path: str) -> pd.DataFrame:
    incoming = pd.read_csv(path)
    incoming = _coerce_types(incoming)
    # Simple append; avoid id collisions by reassigning ids
    df = load_trades()
    start_id = next_trade_id(df)
    if not incoming.empty:
        incoming = incoming.copy()
        incoming = incoming.sort_values("trade_datetime")
        incoming["id"] = list(range(start_id, start_id + len(incoming)))
        df = pd.concat([df, incoming], ignore_index=True)
        df = _coerce_types(df)
        df = df.sort_values("trade_datetime").reset_index(drop=True)
        save_trades(df)
    return df