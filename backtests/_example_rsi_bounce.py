"""
Example Backtest: RSI Oversold Bounce Strategy

TradingView Indicator: (example - RSI based)
Logic:
  - Buy when RSI(14) crosses below 30 (oversold)
  - Sell when RSI(14) crosses above 70 (overbought)

This file serves as a reference for the agent when converting
Pine Script indicators to Python backtests.
"""

import sys
import os
import json

import pandas as pd
import ta
from backtesting import Backtest, Strategy

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.data_loader import load_data

INDICATOR_NAME = "RSI Oversold Bounce"


class MyStrategy(Strategy):
    # Strategy parameters (can be optimized)
    rsi_window = 14
    oversold = 30
    overbought = 70

    def init(self):
        # Use self.I() wrapper - pass function + arguments, NOT pre-computed values
        self.rsi = self.I(
            ta.momentum.rsi,
            pd.Series(self.data.Close),
            window=self.rsi_window,
        )

    def next(self):
        # Skip if RSI not yet computed (NaN at start)
        if len(self.rsi) < 2 or pd.isna(self.rsi[-1]):
            return

        # Buy: RSI crosses below oversold level
        if not self.position:
            if self.rsi[-1] < self.oversold:
                self.buy()

        # Sell: RSI crosses above overbought level
        elif self.position:
            if self.rsi[-1] > self.overbought:
                self.position.close()


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

    print(json.dumps(results))
    return results


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    run_backtest(ticker=ticker)
