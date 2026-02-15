"""
=== ORB (Opening Range Breakout) Strategy ===
Converted from TradingView: ORB + Key Session Levels Strategy
Uses 20-day high/low breakout as proxy for ORB on daily data
"""

import sys
import os
import json

import pandas as pd
import ta
from backtesting import Backtest, Strategy

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.data_loader import load_data

INDICATOR_NAME = "ORB + Key Session Levels Strategy"


class MyStrategy(Strategy):
    """20-day breakout strategy"""
    lookback = 20
    
    def init(self):
        # Rolling high/low using ta library
        self.roll_high = self.I(
            ta.volatility.bollinger_hband, 
            pd.Series(self.data.Close), 
            window=self.lookback, 
            window_dev=0
        )
        self.roll_low = self.I(
            ta.volatility.bollinger_lband,
            pd.Series(self.data.Close), 
            window=self.lookback, 
            window_dev=0
        )
    
    def next(self):
        if len(self.data) < self.lookback + 5:
            return
        
        rh = self.roll_high[-1]
        rl = self.roll_low[-1]
        
        if pd.isna(rh) or pd.isna(rl):
            return
        
        close = self.data.Close[-1]
        
        # Entry signals
        if not self.position:
            if close > rh:
                self.buy()
            elif close < rl:
                self.sell()
        # Exit on opposite signal
        else:
            if self.position.is_long and close < rl:
                self.position.close()
            elif self.position.is_short and close > rh:
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
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("ticker", nargs="?", default="SPY")
    parser.add_argument("--cash", type=float, default=100000)
    args = parser.parse_args()

    run_backtest(args.ticker, args.cash)
