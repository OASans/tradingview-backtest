# TradingView Indicator Auto-Backtest System

Automated system that browses TradingView community indicators, extracts Pine Script source code, converts them to Python backtests, and runs them against SPY/QQQ data to find strategies with alpha.

Inspired by [Moon Dev](https://www.youtube.com/@moondevonyt)'s workflow.

## How It Works

1. **Browse** TradingView Editor's Picks and community indicators
2. **Extract** Pine Script source code from open-source indicators
3. **Convert** Pine Script logic to Python using `backtesting.py` + `ta` library
4. **Backtest** against 2 years of SPY/QQQ daily data ($100k initial, 0.1% commission)
5. **Record** all results to `results/master_results.csv`
6. **Notify** via Discord webhook when a strategy passes quality thresholds

## Quality Thresholds (for Discord alerts)

- Return > 20%
- Max Drawdown > -30%
- Number of Trades >= 20
- Win Rate > 45%
- Profit Factor > 1.3

## Project Structure

```
├── PROJECT_INSTRUCTIONS.md   # Agent operations manual
├── scripts/
│   ├── backtest_template.py   # Backtest template (copy to create new)
│   ├── run_single_backtest.py # Runner (execute + record to CSV)
│   ├── discord_notify.py      # Discord webhook notifications
│   └── data_loader.py         # yfinance data downloader with caching
├── pine_scripts/              # Original Pine Script source code
├── backtests/                 # Converted Python backtests
│   └── _example_rsi_bounce.py # Reference example
├── results/
│   └── master_results.csv     # All backtest results
└── logs/
    ├── scrape_log.csv         # Scraping progress
    └── errors.log             # Error log
```

## Quick Start

```bash
# Install dependencies
pip install Backtesting ta discord-webhook yfinance

# Run the example backtest
python3 scripts/run_single_backtest.py backtests/_example_rsi_bounce.py SPY

# Check results
cat results/master_results.csv
```

## Tech Stack

- **[backtesting.py](https://kernc.github.io/backtesting.py/)** — backtest framework
- **[ta](https://technical-analysis-library-in-python.readthedocs.io/)** — technical indicators (RSI, MACD, BB, etc.)
- **[yfinance](https://github.com/ranaroussi/yfinance)** — market data (SPY, QQQ)
- **[discord-webhook](https://github.com/lovvskillz/python-discord-webhook)** — Discord notifications

## Environment

- Python 3.10 on ARM64 (Orange Pi / RK3588)
- Designed to run autonomously via OpenClaw agent
