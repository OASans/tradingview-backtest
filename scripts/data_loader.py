"""
Data loader with caching for yfinance data.
Downloads and caches stock data to avoid repeated API calls.
"""

import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data_cache")


def load_data(ticker="SPY", years=2):
    """
    Download daily OHLCV data via yfinance with local CSV caching.

    Returns a DataFrame with columns: Open, High, Low, Close, Volume
    Index is a timezone-naive DatetimeIndex named 'Date'.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{ticker}_{years}y.csv")

    # Use cache if it exists and is less than 24 hours old
    if os.path.exists(cache_file):
        mtime = os.path.getmtime(cache_file)
        age_hours = (datetime.now().timestamp() - mtime) / 3600
        if age_hours < 24:
            df = pd.read_csv(cache_file, index_col="Date", parse_dates=True)
            if len(df) > 100:
                return df

    # Download fresh data
    end = datetime.now()
    start = end - timedelta(days=years * 365)

    data = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                       end=end.strftime("%Y-%m-%d"), auto_adjust=True)

    if data.empty:
        raise ValueError(f"No data returned for {ticker}")

    # Handle MultiIndex columns (yfinance sometimes returns multi-level)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Keep only OHLCV
    df = data[["Open", "High", "Low", "Close", "Volume"]].copy()

    # Remove timezone info from index
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)

    df.index.name = "Date"

    # Cache to CSV
    df.to_csv(cache_file)

    return df


if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "SPY"
    df = load_data(ticker)
    print(f"Loaded {len(df)} rows for {ticker}")
    print(f"Date range: {df.index[0]} to {df.index[-1]}")
    print(df.tail())
