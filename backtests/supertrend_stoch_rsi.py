"""
=== Super Trend + RSI Strategy ===
Converted from TradingView Pine Script
"""

import sys
import os
import json

import pandas as pd
import ta
from backtesting import Backtest, Strategy

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.data_loader import load_data

INDICATOR_NAME = "Super Trend + RSI"


class MyStrategy(Strategy):
    # Use exact format from working example
    sma_window = 50
    rsi_window = 14
    rsi_oversold = 50
    rsi_overbought = 65

    def init(self):
        self.sma = self.I(
            ta.trend.sma_indicator,
            pd.Series(self.data.Close),
            window=self.sma_window,
        )
        self.rsi = self.I(
            ta.momentum.rsi,
            pd.Series(self.data.Close),
            window=self.rsi_window,
        )

    def next(self):
        if len(self.rsi) < 2 or pd.isna(self.rsi[-1]) or pd.isna(self.sma[-1]):
            return

        close = self.data.Close[-1]
        trend_up = close > self.sma[-1]

        # Buy: uptrend + RSI pullback
        if not self.position:
            if trend_up and self.rsi[-1] < self.rsi_oversold:
                self.buy()
        # Sell: trend breaks down or RSI overbought
        elif self.position:
            if not trend_up or self.rsi[-1] > self.rsi_overbought:
                self.position.close()


def run_backtest(ticker="SPY", cash=100000, commission=0.001):
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker", nargs="?", default="SPY")
    parser.add_argument("--cash", type=float, default=100000)
    args = parser.parse_args()

    run_backtest(args.ticker, args.cash)
