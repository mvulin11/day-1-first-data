**Day 1 First Data - Financial Analysis Projects**
This repository contains my Jupyter notebook projects focused on financial data analysis and trading strategies.

📁 Projects
1. Day 1 First Data (day-1-first-data.ipynb)
Initial exploration of stock market data, basic data cleaning and visualization
2. Moving Averages Analysis (Day-1-moving-averages.ipynb)
Implementation and analysis of moving average trading strategies using historical stock data
3. Backtesting Strategy (day-2-backtesting.ipynb)
Backtesting framework for evaluating trading strategy performance over historical periods

🛠️ Requirements
To run these notebooks, you'll need:
bashpip install pandas numpy matplotlib seaborn jupyter
# Add any other specific libraries you use (e.g., yfinance, ta-lib, etc.)
🚀 Getting Started

Clone this repository:
bashgit clone https://github.com/mvulin11/day-1-first-data.git
cd day-1-first-data

Install the required packages:
bashpip install -r requirements.txt

Launch Jupyter Lab:
bashjupyter lab

Open any of the .ipynb files to explore the analysis

📊 Data Sources
Stock data sourced from Yahoo Finance API

🔄 Future Work

 Add more technical indicators
 Implement additional trading strategies
 Create interactive dashboards
 Add risk management features

# Options Profit Tracker

A simple, local, zero-dependency Python CLI to record option trades and track realized and unrealized P&L using FIFO cost basis. Data is stored in a local SQLite database.

- Realized P&L (FIFO) per contract
- Open positions with manual marks or optional live quotes via yfinance
- Import/export via CSV
- Tags for grouping strategies or accounts

## Quick start

1) Ensure Python 3.9+ is installed.

2) (Optional) Install yfinance if you want automatic marks:
```bash
pip install yfinance
```

3) Initialize the database (defaults to `./options_tracker.db` or set `OPTIONS_TRACKER_DB`):
```bash
python main.py init
```

4) Add trades:
```bash
python main.py add \
  --datetime 2025-01-10T15:32:00 \
  --symbol AAPL --expiry 2025-02-21 --strike 200 --right C \
  --action BUY --quantity 1 --price 2.35 \
  --commission 0.65 --fees 0.00 --multiplier 100 \
  --tag earnings-call

python main.py add \
  --datetime 2025-01-12T10:05:00 \
  --symbol AAPL --expiry 2025-02-21 --strike 200 --right C \
  --action SELL --quantity 1 --price 3.10 \
  --commission 0.65 --fees 0.00 --multiplier 100 \
  --tag earnings-call
```

5) View positions and realized P&L:
```bash
python main.py positions
python main.py report --from 2025-01-01 --to 2025-12-31
```

6) Set manual marks for open positions:
```bash
python main.py update-mark --symbol AAPL --expiry 2025-02-21 --strike 200 --right C --mark 2.75
```

7) (Optional) Fetch marks using yfinance:
```bash
python main.py fetch-marks
```

8) Import trades from CSV (header must include the shown columns):
```csv
datetime,symbol,expiry,strike,right,action,quantity,price,commission,fees,multiplier,tag
2025-01-10T15:32:00,AAPL,2025-02-21,200,C,BUY,1,2.35,0.65,0.00,100,earnings-call
2025-01-12T10:05:00,AAPL,2025-02-21,200,C,SELL,1,3.10,0.65,0.00,100,earnings-call
```
```bash
python main.py import-csv --path ./trades.csv
```

## Environment
- Database path: set `OPTIONS_TRACKER_DB` to override default `./options_tracker.db`.

## Notes
- Realized P&L includes proportional open/close fees and commissions allocated by matched quantity.
- Unrealized P&L uses manual mark or, if available, yfinance mid price (bid/ask/last fallback). Closing fees are unknown; unrealized P&L excludes yet-to-be-incurred closing costs.
- Right must be `C` or `P`. Action must be `BUY` or `SELL`.
