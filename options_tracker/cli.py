import argparse
import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from . import __version__
from . import db
from .calculations import OptionContract, Trade, build_positions, parse_trade_row
from .yf_client import try_fetch_mark


def _print_table(headers: List[str], rows: List[List[object]]) -> None:
    # Simple fixed-width table printer (no external deps)
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    def fmt_row(vals: List[object]) -> str:
        return " | ".join(str(vals[i]).ljust(col_widths[i]) for i in range(len(vals)))

    print(fmt_row(headers))
    print("-+-".join("-" * w for w in col_widths))
    for row in rows:
        print(fmt_row(row))


def cmd_init(_: argparse.Namespace) -> None:
    db.init_db()
    print(f"Initialized database at {db.get_db_path()}")


def cmd_add(args: argparse.Namespace) -> None:
    record = {
        "datetime": args.datetime,
        "symbol": args.symbol.upper(),
        "expiry": args.expiry,
        "strike": float(args.strike),
        "right": args.right.upper(),
        "action": args.action.upper(),
        "quantity": int(args.quantity),
        "price": float(args.price),
        "commission": float(args.commission or 0.0),
        "fees": float(args.fees or 0.0),
        "multiplier": int(args.multiplier or 100),
        "tag": args.tag,
    }
    inserted_id = db.insert_trade(record)
    print(f"Inserted trade id={inserted_id}")


def cmd_list_trades(_: argparse.Namespace) -> None:
    trades = [parse_trade_row(r) for r in db.fetch_trades()]
    headers = [
        "id",
        "datetime",
        "symbol",
        "expiry",
        "strike",
        "right",
        "action",
        "qty",
        "price",
        "comm",
        "fees",
        "mult",
        "tag",
    ]
    rows: List[List[object]] = []
    for t in trades:
        rows.append([
            t.id,
            t.dt.isoformat(timespec="seconds"),
            t.contract.symbol,
            t.contract.expiry,
            f"{t.contract.strike:g}",
            t.contract.right,
            t.action,
            t.quantity,
            f"{t.price:.2f}",
            f"{t.commission:.2f}",
            f"{t.fees:.2f}",
            t.contract.multiplier,
            t.tag or "",
        ])
    _print_table(headers, rows)


def _latest_mark_for(contract: OptionContract) -> Optional[float]:
    latest = db.get_latest_mark(contract.symbol, contract.expiry, contract.strike, contract.right)
    return latest[0] if latest else None


def cmd_positions(_: argparse.Namespace) -> None:
    trades = [parse_trade_row(r) for r in db.fetch_trades()]
    positions, total_realized, _ = build_positions(trades)

    headers = [
        "symbol",
        "expiry",
        "strike",
        "right",
        "net",
        "mark",
        "unrealized",
        "realized_total",
    ]
    rows: List[List[object]] = []
    for pos in positions.values():
        if pos.net_quantity == 0 and not pos.open_lots:
            continue
        mark = _latest_mark_for(pos.contract)
        unreal = pos.current_unrealized(mark)
        rows.append([
            pos.contract.symbol,
            pos.contract.expiry,
            f"{pos.contract.strike:g}",
            pos.contract.right,
            pos.net_quantity,
            f"{mark:.2f}" if mark is not None else "",
            f"{unreal:.2f}" if unreal is not None else "",
            f"{pos.realized_pnl:.2f}",
        ])

    _print_table(headers, rows)
    print(f"\nTotal realized P&L: {total_realized:.2f}")


def cmd_report(args: argparse.Namespace) -> None:
    trades_rows = db.fetch_trades_window(args.from_dt, args.to_dt)
    trades = [parse_trade_row(r) for r in trades_rows]
    positions, total_realized, fills = build_positions(trades)

    print(f"Realized P&L ({args.from_dt or '-inf'} .. {args.to_dt or '+inf'}): {total_realized:.2f}")

    # By symbol summary
    sym_realized: Dict[str, float] = {}
    for f in fills:
        sym_realized[f.contract.symbol] = sym_realized.get(f.contract.symbol, 0.0) + f.realized_pnl

    headers = ["symbol", "realized"]
    rows = [[sym, f"{pnl:.2f}"] for sym, pnl in sorted(sym_realized.items())]
    _print_table(headers, rows)


def cmd_update_mark(args: argparse.Namespace) -> None:
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    db.upsert_mark(
        symbol=args.symbol.upper(),
        expiry=args.expiry,
        strike=float(args.strike),
        right=args.right.upper(),
        mark=float(args.mark),
        updated_at=now,
    )
    print("Mark updated.")


def cmd_fetch_marks(_: argparse.Namespace) -> None:
    trades = [parse_trade_row(r) for r in db.fetch_trades()]
    seen: set[Tuple[str, str, float, str]] = set()
    updated = 0
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    for t in trades:
        key = t.contract.key()
        if key in seen:
            continue
        seen.add(key)
        mark = try_fetch_mark(*key)
        if mark is None:
            continue
        db.upsert_mark(t.contract.symbol, t.contract.expiry, t.contract.strike, t.contract.right, mark, now)
        updated += 1

    print(f"Fetched marks for {updated} contracts.")


def cmd_import_csv(args: argparse.Namespace) -> None:
    path = args.path
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        required = [
            "datetime",
            "symbol",
            "expiry",
            "strike",
            "right",
            "action",
            "quantity",
            "price",
            "commission",
            "fees",
            "multiplier",
            "tag",
        ]
        missing = [c for c in required if c not in reader.fieldnames]
        if missing:
            raise SystemExit(f"CSV missing required columns: {missing}")
        batch: List[Dict] = []
        for row in reader:
            batch.append({
                "datetime": row["datetime"],
                "symbol": row["symbol"].upper(),
                "expiry": row["expiry"],
                "strike": float(row["strike"]),
                "right": row["right"].upper(),
                "action": row["action"].upper(),
                "quantity": int(row["quantity"]),
                "price": float(row["price"]),
                "commission": float(row.get("commission", 0.0) or 0.0),
                "fees": float(row.get("fees", 0.0) or 0.0),
                "multiplier": int(row.get("multiplier", 100) or 100),
                "tag": row.get("tag") or None,
            })
        inserted = db.insert_trades(batch)
        print(f"Imported {inserted} trades from {path}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="options-tracker", description="Options Profit Tracker (FIFO) - local SQLite")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("init", help="Initialize the database")
    sp.set_defaults(func=cmd_init)

    sp = sub.add_parser("add", help="Add a trade record")
    sp.add_argument("--datetime", required=True, help="ISO datetime, e.g., 2025-01-10T15:32:00")
    sp.add_argument("--symbol", required=True)
    sp.add_argument("--expiry", required=True, help="Option expiry YYYY-MM-DD")
    sp.add_argument("--strike", required=True, type=float)
    sp.add_argument("--right", required=True, choices=["C", "P", "c", "p"])
    sp.add_argument("--action", required=True, choices=["BUY", "SELL", "buy", "sell"])
    sp.add_argument("--quantity", required=True, type=int)
    sp.add_argument("--price", required=True, type=float)
    sp.add_argument("--commission", type=float, default=0.0)
    sp.add_argument("--fees", type=float, default=0.0)
    sp.add_argument("--multiplier", type=int, default=100)
    sp.add_argument("--tag")
    sp.set_defaults(func=cmd_add)

    sp = sub.add_parser("list-trades", help="List all trades")
    sp.set_defaults(func=cmd_list_trades)

    sp = sub.add_parser("positions", help="Show open positions, unrealized and realized totals")
    sp.set_defaults(func=cmd_positions)

    sp = sub.add_parser("report", help="Realized P&L over time window")
    sp.add_argument("--from", dest="from_dt", help="From datetime (inclusive, ISO)")
    sp.add_argument("--to", dest="to_dt", help="To datetime (inclusive, ISO)")
    sp.set_defaults(func=cmd_report)

    sp = sub.add_parser("update-mark", help="Set a manual mark for a contract")
    sp.add_argument("--symbol", required=True)
    sp.add_argument("--expiry", required=True)
    sp.add_argument("--strike", required=True, type=float)
    sp.add_argument("--right", required=True, choices=["C", "P", "c", "p"])
    sp.add_argument("--mark", required=True, type=float)
    sp.set_defaults(func=cmd_update_mark)

    sp = sub.add_parser("fetch-marks", help="Try to fetch marks for seen contracts via yfinance (optional)")
    sp.set_defaults(func=cmd_fetch_marks)

    sp = sub.add_parser("import-csv", help="Import trades from CSV")
    sp.add_argument("--path", required=True)
    sp.set_defaults(func=cmd_import_csv)

    return p


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    # Validate right/action canonical forms
    if hasattr(args, "right"):
        args.right = args.right.upper()
    if hasattr(args, "action"):
        args.action = args.action.upper()
    args.func(args)