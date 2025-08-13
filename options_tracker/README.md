# Options Profit Tracker

A simple local Streamlit app to track options trades and compute realized and unrealized P/L using FIFO lot matching.

## Features
- Add, edit, delete trades (BTO, STO, STC, BTC)
- CSV storage at `/workspace/options_tracker/trades.csv`
- Realized P/L with fees included and options multiplier (100)
- Open positions with average cost
- Enter manual marks to estimate unrealized P/L
- Import/Export CSV

## Quick start

```bash
# From the container shell
python -m pip install -r /workspace/options_tracker/requirements.txt
streamlit run /workspace/options_tracker/app.py --server.port 8501 --server.address 0.0.0.0
```

Then open the URL printed by Streamlit in your browser.

## CSV schema
Columns in `trades.csv`:

- `id` (int): unique row id
- `group_id` (int, optional): strategy group
- `symbol` (str): underlying ticker
- `expiry` (date): YYYY-MM-DD
- `strike` (float)
- `option_type` ("C" or "P")
- `action` ("BTO", "STO", "STC", "BTC")
- `quantity` (int): number of contracts
- `price` (float): per option
- `fees` (float)
- `trade_datetime` (timestamp): local time
- `note` (str)

## Notes
- Realized P/L uses per-leg FIFO matching. It handles partial fills and allocates fees pro-rata.
- Unrealized P/L is based on user-input marks; there is no data feed.
- All P/L amounts reflect the 100x options multiplier.