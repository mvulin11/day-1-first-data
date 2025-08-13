from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class OptionContract:
    symbol: str
    expiry: str  # YYYY-MM-DD
    strike: float
    right: str  # 'C' or 'P'
    multiplier: int = 100

    def key(self) -> Tuple[str, str, float, str]:
        return (self.symbol, self.expiry, float(self.strike), self.right)


@dataclass
class Trade:
    id: int
    dt: datetime
    contract: OptionContract
    action: str  # 'BUY' or 'SELL'
    quantity: int
    price: float  # price per contract
    commission: float
    fees: float
    tag: Optional[str]

    @property
    def signed_quantity(self) -> int:
        return self.quantity if self.action.upper() == "BUY" else -self.quantity


@dataclass
class OpenLot:
    remaining_qty: int  # sign indicates long(+)/short(-)
    open_price: float
    open_fee_total: float  # total $ associated with the original lot
    trade_ref: int


@dataclass
class RealizedFill:
    contract: OptionContract
    realized_pnl: float
    quantity_closed: int
    open_trade_id: int
    close_trade_id: int


@dataclass
class Position:
    contract: OptionContract
    net_quantity: int
    open_lots: List[OpenLot]
    realized_pnl: float
    tag_counts: Dict[str, int]

    def current_unrealized(self, mark: Optional[float]) -> Optional[float]:
        if mark is None:
            return None
        unrealized = 0.0
        for lot in self.open_lots:
            if lot.remaining_qty == 0:
                continue
            sign = 1 if lot.remaining_qty > 0 else -1
            qty = abs(lot.remaining_qty)
            # Price P&L
            unrealized += (mark - lot.open_price) * self.contract.multiplier * qty * sign
            # Subtract the proportional open fees that are still embedded in the lot
            # Note: closing fees are unknown and therefore excluded
            open_fee_per_contract = lot.open_fee_total / max(1, abs(lot.remaining_qty))
            unrealized -= open_fee_per_contract * qty
        return unrealized


def parse_trade_row(row) -> Trade:
    dt = datetime.fromisoformat(str(row["datetime"]))
    contract = OptionContract(
        symbol=str(row["symbol"]),
        expiry=str(row["expiry"]),
        strike=float(row["strike"]),
        right=str(row["right"]).upper(),
        multiplier=int(row["multiplier"]),
    )
    return Trade(
        id=int(row["id"]) if "id" in row.keys() else -1,
        dt=dt,
        contract=contract,
        action=str(row["action"]).upper(),
        quantity=int(row["quantity"]),
        price=float(row["price"]),
        commission=float(row["commission"]),
        fees=float(row["fees"]),
        tag=str(row["tag"]) if row["tag"] is not None else None,
    )


def build_positions(trades: Iterable[Trade]) -> Tuple[Dict[Tuple[str, str, float, str], Position], float, List[RealizedFill]]:
    positions: Dict[Tuple[str, str, float, str], Position] = {}
    total_realized = 0.0
    fills: List[RealizedFill] = []

    # Ensure chronological
    sorted_trades = sorted(trades, key=lambda t: (t.dt, t.id))

    for trade in sorted_trades:
        key = trade.contract.key()
        if key not in positions:
            positions[key] = Position(
                contract=trade.contract,
                net_quantity=0,
                open_lots=[],
                realized_pnl=0.0,
                tag_counts={},
            )
        pos = positions[key]

        # Tag counts (for simple grouping visibility)
        if trade.tag:
            pos.tag_counts[trade.tag] = pos.tag_counts.get(trade.tag, 0) + trade.quantity

        sign_trade = 1 if trade.action == "BUY" else -1
        qty_to_process = trade.quantity * sign_trade  # signed qty
        close_trade_fee_total = trade.commission + trade.fees

        def add_open_lot(qty_signed: int):
            pos.open_lots.append(
                OpenLot(
                    remaining_qty=qty_signed,
                    open_price=trade.price,
                    open_fee_total=close_trade_fee_total,
                    trade_ref=trade.id,
                )
            )

        # If no net or same direction, just open
        if pos.net_quantity == 0 or (pos.net_quantity > 0 and qty_to_process > 0) or (pos.net_quantity < 0 and qty_to_process < 0):
            add_open_lot(qty_to_process)
            pos.net_quantity += qty_to_process
            continue

        # We are closing against existing lots (opposite signs)
        qty_remaining_to_close = abs(qty_to_process)
        closing_side_is_buy = qty_to_process > 0  # buy-to-close for short position

        i = 0
        while qty_remaining_to_close > 0 and i < len(pos.open_lots):
            lot = pos.open_lots[i]
            if (lot.remaining_qty > 0 and not closing_side_is_buy) or (lot.remaining_qty < 0 and closing_side_is_buy):
                # This lot is the opposite side; we can close against it
                lot_qty_abs = abs(lot.remaining_qty)
                matched = min(lot_qty_abs, qty_remaining_to_close)

                # Determine realized P&L for the matched portion
                lot_sign = 1 if lot.remaining_qty > 0 else -1
                price_diff = (trade.price - lot.open_price) * lot_sign
                realized_gross = price_diff * trade.contract.multiplier * matched

                # Allocate fees proportionally
                open_fee_per_contract = lot.open_fee_total / lot_qty_abs
                close_fee_per_contract = close_trade_fee_total / abs(trade.quantity)
                fees_for_matched = (open_fee_per_contract + close_fee_per_contract) * matched

                realized_net = realized_gross - fees_for_matched

                pos.realized_pnl += realized_net
                total_realized += realized_net
                fills.append(
                    RealizedFill(
                        contract=trade.contract,
                        realized_pnl=realized_net,
                        quantity_closed=matched,
                        open_trade_id=lot.trade_ref,
                        close_trade_id=trade.id,
                    )
                )

                # Reduce the lot and the remaining close qty
                if matched == lot_qty_abs:
                    lot.remaining_qty = 0
                else:
                    lot.remaining_qty = lot_sign * (lot_qty_abs - matched)
                qty_remaining_to_close -= matched
                pos.net_quantity -= lot_sign * matched

                if lot.remaining_qty == 0:
                    i += 1
            else:
                # Same side lot; skip
                i += 1

        # If we still have more of the closing trade than open lots provided, the remaining becomes a new open lot (flips side)
        if qty_remaining_to_close > 0:
            # Remaining is actually opening on the other side
            opening_sign = 1 if closing_side_is_buy else -1
            add_open_lot(opening_sign * qty_remaining_to_close)
            pos.net_quantity += opening_sign * qty_remaining_to_close

    # Prune empty open lots for cleanliness
    for pos in positions.values():
        pos.open_lots = [lot for lot in pos.open_lots if lot.remaining_qty != 0]

    return positions, total_realized, fills