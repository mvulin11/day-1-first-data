from typing import Optional


def try_fetch_mark(symbol: str, expiry: str, strike: float, right: str) -> Optional[float]:
    """Attempt to fetch an option mark from yfinance.

    Returns mid price (bid/ask average) if available, else lastPrice, else None.
    """
    try:
        import yfinance as yf
    except Exception:
        return None

    try:
        t = yf.Ticker(symbol)
        # yfinance expects expiry as YYYY-MM-DD
        chain = t.option_chain(expiry)
        df = chain.calls if right.upper() == "C" else chain.puts
        # Filter exact strike match
        matches = df[df["strike"] == float(strike)]
        if matches.empty:
            return None
        row = matches.iloc[0]
        bid = float(row.get("bid", 0.0) or 0.0)
        ask = float(row.get("ask", 0.0) or 0.0)
        last = float(row.get("lastPrice", 0.0) or 0.0)
        if bid and ask and ask >= bid:
            return (bid + ask) / 2.0
        if last:
            return last
        return None
    except Exception:
        return None