#!/usr/bin/env python3
"""
Run a single backtest script and record results to master_results.csv.

Usage:
    python3 scripts/run_single_backtest.py backtests/my_strategy.py SPY
    python3 scripts/run_single_backtest.py backtests/my_strategy.py QQQ
"""

import subprocess
import sys
import os
import json
import csv
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_CSV = os.path.join(PROJECT_ROOT, "results", "master_results.csv")
ERROR_LOG = os.path.join(PROJECT_ROOT, "logs", "errors.log")
TIMEOUT = 120  # seconds


def log_error(script_path, ticker, error_msg):
    """Append error to errors.log."""
    with open(ERROR_LOG, "a") as f:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {script_path} | {ticker} | {error_msg}\n")


def append_result(result, script_path):
    """Append a result dict to master_results.csv."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row = {
        "indicator_name": result.get("indicator_name", "unknown"),
        "ticker": result.get("ticker", "unknown"),
        "return_pct": result.get("return_pct", 0),
        "buy_hold_return_pct": result.get("buy_hold_return_pct", 0),
        "max_drawdown_pct": result.get("max_drawdown_pct", 0),
        "num_trades": result.get("num_trades", 0),
        "win_rate_pct": result.get("win_rate_pct", 0),
        "profit_factor": result.get("profit_factor", 0),
        "sharpe_ratio": result.get("sharpe_ratio", 0),
        "start_date": result.get("start_date", ""),
        "end_date": result.get("end_date", ""),
        "script_file": os.path.basename(script_path),
        "timestamp": ts,
    }

    file_exists = os.path.exists(RESULTS_CSV) and os.path.getsize(RESULTS_CSV) > 0
    with open(RESULTS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

    return row


def run_backtest(script_path, ticker="SPY"):
    """Execute a backtest script and capture its JSON output."""
    script_path = os.path.abspath(script_path)

    if not os.path.exists(script_path):
        error = f"Script not found: {script_path}"
        log_error(script_path, ticker, error)
        print(f"ERROR: {error}", file=sys.stderr)
        return None

    print(f"Running: {os.path.basename(script_path)} on {ticker}...")

    try:
        result = subprocess.run(
            [sys.executable, script_path, ticker],
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            cwd=PROJECT_ROOT,
        )

        if result.returncode != 0:
            error = result.stderr.strip()[-500:] if result.stderr else "Unknown error"
            log_error(script_path, ticker, error)
            print(f"FAILED: {error}", file=sys.stderr)
            return None

        # Parse JSON from the last line of stdout
        stdout_lines = result.stdout.strip().split("\n")
        json_line = None
        for line in reversed(stdout_lines):
            line = line.strip()
            if line.startswith("{"):
                json_line = line
                break

        if not json_line:
            error = f"No JSON output found. stdout: {result.stdout[:300]}"
            log_error(script_path, ticker, error)
            print(f"FAILED: {error}", file=sys.stderr)
            return None

        data = json.loads(json_line)
        row = append_result(data, script_path)

        # Print summary
        print(f"  Return: {row['return_pct']}%  |  "
              f"B&H: {row['buy_hold_return_pct']}%  |  "
              f"MaxDD: {row['max_drawdown_pct']}%  |  "
              f"Trades: {row['num_trades']}  |  "
              f"WinRate: {row['win_rate_pct']}%  |  "
              f"PF: {row['profit_factor']}  |  "
              f"Sharpe: {row['sharpe_ratio']}")

        return data

    except subprocess.TimeoutExpired:
        error = f"Timeout after {TIMEOUT}s"
        log_error(script_path, ticker, error)
        print(f"TIMEOUT: {error}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        error = f"JSON parse error: {e}"
        log_error(script_path, ticker, error)
        print(f"FAILED: {error}", file=sys.stderr)
        return None
    except Exception as e:
        error = str(e)
        log_error(script_path, ticker, error)
        print(f"ERROR: {error}", file=sys.stderr)
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/run_single_backtest.py <script.py> [TICKER]")
        sys.exit(1)

    script = sys.argv[1]
    ticker = sys.argv[2] if len(sys.argv) > 2 else "SPY"
    result = run_backtest(script, ticker)

    if result is None:
        sys.exit(1)
