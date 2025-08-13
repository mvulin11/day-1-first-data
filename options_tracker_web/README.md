# Options Profit Tracker (Web)

A zero-dependency, client-side options P/L tracker. Data stays in your browser localStorage. Implements FIFO matching, realized and unrealized P/L with a 100x options multiplier.

## Run

```bash
python3 -m http.server 8080 -d /workspace/options_tracker_web
```

Open the served URL in your browser.

## Notes
- Import/Export CSV using the toolbar in the Trades tab.
- Timestamps use your local timezone via the browser.
- This is a simple local tool; no market data feed.