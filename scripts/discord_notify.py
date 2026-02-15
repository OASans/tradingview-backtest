#!/usr/bin/env python3
"""
Discord webhook notification for high-quality backtest results.

Usage:
    # Notify about a specific result (pass JSON string):
    python3 scripts/discord_notify.py '{"indicator_name": "RSI Bounce", "ticker": "SPY", ...}'

    # Or import and call from another script:
    from scripts.discord_notify import check_and_notify
    check_and_notify(result_dict)

Set DISCORD_WEBHOOK_URL environment variable or edit WEBHOOK_URL below.
"""

import os
import sys
import json

from discord_webhook import DiscordWebhook, DiscordEmbed

# Set your webhook URL here or use DISCORD_WEBHOOK_URL env var
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# Quality thresholds - strategy must pass ALL to trigger notification
THRESHOLDS = {
    "return_pct": 20.0,         # Return > 20%
    "max_drawdown_pct": -30.0,  # Max Drawdown > -30% (less negative)
    "num_trades": 20,           # At least 20 trades
    "win_rate_pct": 45.0,       # Win rate > 45%
    "profit_factor": 1.3,       # Profit factor > 1.3
}


def passes_quality_check(result):
    """Check if a backtest result passes all quality thresholds."""
    checks = {
        "return_pct": result.get("return_pct", 0) > THRESHOLDS["return_pct"],
        "max_drawdown_pct": result.get("max_drawdown_pct", -100) > THRESHOLDS["max_drawdown_pct"],
        "num_trades": result.get("num_trades", 0) >= THRESHOLDS["num_trades"],
        "win_rate_pct": result.get("win_rate_pct", 0) > THRESHOLDS["win_rate_pct"],
        "profit_factor": result.get("profit_factor", 0) > THRESHOLDS["profit_factor"],
    }
    return all(checks.values()), checks


def send_notification(result):
    """Send a Discord embed notification for a good strategy."""
    if not WEBHOOK_URL:
        print("WARNING: DISCORD_WEBHOOK_URL not set. Skipping notification.",
              file=sys.stderr)
        return False

    webhook = DiscordWebhook(url=WEBHOOK_URL)

    embed = DiscordEmbed(
        title=f"Alpha Found: {result.get('indicator_name', 'Unknown')}",
        description=f"Ticker: **{result.get('ticker', 'N/A')}**",
        color="03b2f8",
    )

    embed.add_embed_field(name="Return", value=f"{result.get('return_pct', 0)}%", inline=True)
    embed.add_embed_field(name="Buy & Hold", value=f"{result.get('buy_hold_return_pct', 0)}%", inline=True)
    embed.add_embed_field(name="Max Drawdown", value=f"{result.get('max_drawdown_pct', 0)}%", inline=True)
    embed.add_embed_field(name="Trades", value=str(result.get("num_trades", 0)), inline=True)
    embed.add_embed_field(name="Win Rate", value=f"{result.get('win_rate_pct', 0)}%", inline=True)
    embed.add_embed_field(name="Profit Factor", value=str(result.get("profit_factor", 0)), inline=True)
    embed.add_embed_field(name="Sharpe Ratio", value=str(result.get("sharpe_ratio", 0)), inline=True)

    if result.get("script_file"):
        embed.set_footer(text=f"Script: {result['script_file']}")

    embed.set_timestamp()
    webhook.add_embed(embed)

    response = webhook.execute()
    if response and response.status_code in (200, 204):
        print(f"Discord notification sent for: {result.get('indicator_name')}")
        return True
    else:
        print(f"Discord notification failed: {response.status_code if response else 'No response'}",
              file=sys.stderr)
        return False


def check_and_notify(result):
    """Check quality thresholds and send notification if passed."""
    passed, checks = passes_quality_check(result)

    if passed:
        print(f"QUALITY CHECK PASSED for {result.get('indicator_name')}")
        send_notification(result)
        return True
    else:
        failed = [k for k, v in checks.items() if not v]
        print(f"Quality check failed for {result.get('indicator_name')}: {failed}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/discord_notify.py '<json_result>'")
        print("   or: DISCORD_WEBHOOK_URL=... python3 scripts/discord_notify.py '<json>'")
        sys.exit(1)

    try:
        result = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        print(f"Invalid JSON: {sys.argv[1]}", file=sys.stderr)
        sys.exit(1)

    check_and_notify(result)
