from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import pandas as pd

OPTIONS_MULTIPLIER = 100.0


@dataclass
class Lot:
    quantity: int
    price: float
    fees: float


@dataclass
class OpenPosition:
    symbol: str
    expiry: pd.Timestamp
    strike: float
    option_type: str
    side: str  # "LONG" or "SHORT"
    open_quantity: int
    average_cost: float  # per option, excluding multiplier
    total_fees: float


@dataclass
class RealizedEvent:
    symbol: str
    expiry: pd.Timestamp
    strike: float
    option_type: str
    side: str
    quantity: int
    realized_pl: float
    open_price: float
    close_price: float
    open_fees: float
    close_fees: float
    open_ids: List[int]
    close_id: int


def _leg_key(row: pd.Series) -> Tuple[str, pd.Timestamp, float, str]:
    return (
        row["symbol"],
        pd.to_datetime(row["expiry"]),
        float(row["strike"]),
        str(row["option_type"]).upper(),
    )


def _is_open_action(action: str) -> bool:
    return action in {"BTO", "STO"}


def _is_close_action(action: str) -> bool:
    return action in {"BTC", "STC"}


def _side_for_action(action: str) -> str:
    if action in {"BTO", "STC"}:
        return "LONG"
    return "SHORT"


def compute_pl(trades: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    Compute realized events and open positions from a trades DataFrame.

    Returns (realized_events_df, open_positions_df, total_realized_pl)
    Prices are per-option; multiplier applied in realized_pl.
    Fees are included: open fees increase cost basis; close fees reduce proceeds.
    """
    if trades.empty:
        return (
            pd.DataFrame(columns=[
                "symbol",
                "expiry",
                "strike",
                "option_type",
                "side",
                "quantity",
                "realized_pl",
                "open_price",
                "close_price",
                "open_fees",
                "close_fees",
                "open_ids",
                "close_id",
            ]),
            pd.DataFrame(columns=[
                "symbol",
                "expiry",
                "strike",
                "option_type",
                "side",
                "open_quantity",
                "average_cost",
                "total_fees",
            ]),
            0.0,
        )

    trades = trades.sort_values("trade_datetime").reset_index(drop=True)
    realized_records: List[RealizedEvent] = []
    # For each leg, maintain separate long and short open lots (FIFO)
    open_lots: Dict[Tuple[str, pd.Timestamp, float, str, str], List[Tuple[int, Lot]]] = {}

    for idx, row in trades.iterrows():
        key = _leg_key(row)
        action = str(row["action"]).upper()
        option_side = _side_for_action(action)  # LONG/SHORT side of the position impacted
        quantity: int = int(row["quantity"]) if pd.notna(row["quantity"]) else 0
        price: float = float(row["price"]) if pd.notna(row["price"]) else 0.0
        fees: float = float(row["fees"]) if pd.notna(row["fees"]) else 0.0
        trade_id: int = int(row["id"]) if pd.notna(row["id"]) else -1

        if _is_open_action(action):
            # BTO opens LONG; STO opens SHORT
            lots_key = (*key, option_side)
            lots = open_lots.setdefault(lots_key, [])
            lots.append((trade_id, Lot(quantity=quantity, price=price, fees=fees)))
        elif _is_close_action(action):
            # STC closes LONG; BTC closes SHORT
            closing_side = _side_for_action(action)
            lots_key = (*key, closing_side)
            lots = open_lots.setdefault(lots_key, [])
            qty_to_close = quantity
            while qty_to_close > 0 and lots:
                open_trade_id, lot = lots[0]
                matched_qty = min(qty_to_close, lot.quantity)
                # Calculate realized P/L
                if closing_side == "LONG":
                    # Selling to close: proceeds - cost
                    pl_per_contract = (price - lot.price)
                else:
                    # Buying to close a short: open proceeds - repurchase cost
                    pl_per_contract = (lot.price - price)
                # Allocate pro-rata fees
                open_fee_alloc = lot.fees * (matched_qty / lot.quantity if lot.quantity else 1.0)
                close_fee_alloc = fees * (matched_qty / quantity if quantity else 1.0)
                realized_amount = (pl_per_contract * matched_qty * OPTIONS_MULTIPLIER) - open_fee_alloc - close_fee_alloc

                realized_records.append(
                    RealizedEvent(
                        symbol=key[0],
                        expiry=pd.to_datetime(key[1]),
                        strike=key[2],
                        option_type=key[3],
                        side=closing_side,
                        quantity=matched_qty,
                        realized_pl=realized_amount,
                        open_price=lot.price,
                        close_price=price,
                        open_fees=open_fee_alloc,
                        close_fees=close_fee_alloc,
                        open_ids=[open_trade_id],
                        close_id=trade_id,
                    )
                )
                # Reduce or remove lot
                lot.quantity -= matched_qty
                qty_to_close -= matched_qty
                if lot.quantity == 0:
                    lots.pop(0)
                else:
                    lots[0] = (open_trade_id, lot)
            # If qty_to_close remains, it indicates closing more than open; ignore remainder
        else:
            continue

    # Build realized events DataFrame
    realized_df = pd.DataFrame([r.__dict__ for r in realized_records])
    total_realized = float(realized_df["realized_pl"].sum()) if not realized_df.empty else 0.0

    # Build open positions summary
    open_rows: List[OpenPosition] = []
    for lots_key, lots in open_lots.items():
        if not lots:
            continue
        symbol, expiry, strike, option_type, side = lots_key
        total_qty = sum(lot.quantity for _, lot in lots)
        if total_qty == 0:
            continue
        # Weighted average cost and total fees
        total_cost = sum(lot.quantity * lot.price for _, lot in lots)
        total_fees = sum(lot.fees for _, lot in lots)
        average_cost = total_cost / total_qty if total_qty else 0.0
        open_rows.append(
            OpenPosition(
                symbol=symbol,
                expiry=pd.to_datetime(expiry),
                strike=float(strike),
                option_type=str(option_type),
                side=side,
                open_quantity=int(total_qty),
                average_cost=float(average_cost),
                total_fees=float(total_fees),
            )
        )

    open_df = pd.DataFrame([o.__dict__ for o in open_rows])
    return realized_df, open_df, total_realized


def summarize_by_group(trades: pd.DataFrame) -> pd.DataFrame:
    realized_df, open_df, total_realized = compute_pl(trades)
    # Map realized events to group_id via close_id lookup
    if trades.empty:
        return pd.DataFrame(columns=[
            "group_id",
            "realized_pl",
            "open_positions",
        ])
    id_to_group = trades.set_index("id")["group_id"].to_dict()
    if realized_df.empty:
        group_realized = pd.Series(dtype=float)
    else:
        realized_df = realized_df.copy()
        realized_df["group_id"] = realized_df["close_id"].map(id_to_group)
        group_realized = realized_df.groupby("group_id")["realized_pl"].sum()

    # Count open positions per group via latest open trades mapping
    if open_df.empty:
        group_open_counts = pd.Series(dtype=int)
    else:
        # Approximate: count open legs per group by mapping any remaining open trade ids' groups
        # Build a mapping from leg to remaining open quantities and associated open trade ids
        group_counts: Dict[Optional[int], int] = {}
        # Recompute lot keys to capture group via remaining trades
        # Not perfect, but we can estimate by taking last known trade for that leg's group
        for _, o in open_df.iterrows():
            group_counts[None] = group_counts.get(None, 0) + 1
        group_open_counts = pd.Series(group_counts)

    summary = pd.DataFrame({
        "group_id": group_realized.index,
        "realized_pl": group_realized.values,
    })
    # Fill open positions as N/A for now
    if summary.empty:
        summary = pd.DataFrame(columns=["group_id", "realized_pl"])
    return summary


def compute_unrealized(open_positions: pd.DataFrame, marks: pd.DataFrame) -> pd.DataFrame:
    """
    Given open positions and a marks DataFrame with columns:
      symbol, expiry, strike, option_type, side, mark
    compute unrealized P/L per leg and total.
    """
    if open_positions.empty:
        return pd.DataFrame(columns=list(open_positions.columns) + ["mark", "unrealized_pl"])

    key_cols = ["symbol", "expiry", "strike", "option_type", "side"]
    merged = open_positions.merge(marks, on=key_cols, how="left")
    merged["mark"] = pd.to_numeric(merged["mark"], errors="coerce").fillna(merged["average_cost"])

    def _leg_unrealized(row):
        qty = int(row["open_quantity"]) if pd.notna(row["open_quantity"]) else 0
        if row["side"] == "LONG":
            diff = row["mark"] - row["average_cost"]
        else:
            diff = row["average_cost"] - row["mark"]
        return float(diff * qty * OPTIONS_MULTIPLIER)

    merged["unrealized_pl"] = merged.apply(_leg_unrealized, axis=1)
    return merged