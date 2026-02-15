"""
=== BACKTEST TEMPLATE ===

Copy this file to backtests/<indicator_name>.py and fill in:
  1. INDICATOR_NAME - name of the TradingView indicator
  2. MyStrategy.init() - compute indicators using self.I() wrapper
  3. MyStrategy.next() - define buy/sell logic

RULES for self.I() wrapper:
  - self.I() takes a FUNCTION and its ARGUMENTS, NOT pre-computed arrays
  - CORRECT:   self.rsi = self.I(ta.momentum.rsi, self.data.Close, window=14)
  - WRONG:     self.rsi = ta.momentum.rsi(pd.Series(self.data.Close), window=14)
  - For custom calculations, define a helper function that takes arrays and returns an array
  - The function passed to self.I() must return a numpy array or pandas Series

Common ta library indicators:
  - RSI:       ta.momentum.rsi(close, window=14)
  - MACD:      ta.trend.macd_diff(close, window_slow=26, window_fast=12, window_sign=9)
  - SMA:       ta.trend.sma_indicator(close, window=20)
  - EMA:       ta.trend.ema_indicator(close, window=20)
  - BB Upper:  ta.volatility.bollinger_hband(close, window=20, window_dev=2)
  - BB Lower:  ta.volatility.bollinger_lband(close, window=20, window_dev=2)
  - ATR:       ta.volatility.average_true_range(high, low, close, window=14)
  - Stoch %K:  ta.momentum.stoch(high, low, close, window=14, smooth_window=3)
  - ADX:       ta.trend.adx(high, low, close, window=14)
  - CCI:       ta.trend.cci(high, low, close, window=20)
  - OBV:       ta.volume.on_balance_volume(close, volume)
  - VWAP:      ta.volume.volume_weighted_average_price(high, low, close, volume)
  - Williams:  ta.momentum.williams_r(high, low, close, lbp=14)

Usage:
  python3 scripts/run_single_backtest.py backtests/<indicator_name>.py SPY
"""

import sys
import os
import json

import pandas as pd
import ta
from backtesting import Backtest, Strategy

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.data_loader import load_data

# ============================================================
# FILL IN: Indicator name (must match the TradingView indicator)
# ============================================================
INDICATOR_NAME = "TEMPLATE - DO NOT RUN DIRECTLY"


class MyStrategy(Strategy):
    """
    FILL IN: Strategy logic converted from Pine Script.
    """

    def init(self):
        """
        Compute indicators here using self.I() wrapper.

        Example:
            self.rsi = self.I(ta.momentum.rsi, pd.Series(self.data.Close), window=14)
        """
        pass

    def next(self):
        """
        Define buy/sell logic here. Called once per bar.

        Available:
            self.data.Close[-1]  # current close (use negative indexing, -1 = current)
            self.position         # current position object
            self.buy()            # open long position
            self.sell()           # close long position
            self.position.close() # close current position

        Example:
            if not self.position and self.rsi[-1] < 30:
                self.buy()
            elif self.position and self.rsi[-1] > 70:
                self.position.close()
        """
        pass


def run_backtest(ticker="SPY", cash=100000, commission=0.001):
    """Run the backtest and output results as JSON to stdout."""
    df = load_data(ticker, years=2)

    bt = Backtest(df, MyStrategy, cash=cash, commission=commission,
                  exclusive_orders=True)
    stats = bt.run()

    results = {
        "indicator_name": INDICATOR_NAME,
        "ticker": ticker,
        "return_pct": round(float(stats["Return [%]"]), 2),
        "buy_hold_return_pct": round(float(stats["Buy & Hold Return [%]"]), 2),
        "max_drawdown_pct": round(float(stats["Max. Drawdown [%]"]), 2),
        "num_trades": int(stats["# Trades"]),
        "win_rate_pct": round(float(stats["Win Rate [%]"]), 2) if stats["# Trades"] > 0 else 0,
        "profit_factor": round(float(pf), 2) if (pf := stats.get("Profit Factor")) and pf == pf else 0,
        "sharpe_ratio": round(float(sr), 2) if (sr := stats.get("Sharpe Ratio")) and sr == sr else 0,
        "start_date": str(stats["Start"]),
        "end_date": str(stats["End"]),
    }

    # Output JSON to stdout for the runner to capture
    print(json.dumps(results))
    return results


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    run_backtest(ticker=ticker)
