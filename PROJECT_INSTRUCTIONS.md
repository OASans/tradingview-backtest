# TradingView Indicator Auto-Backtest System — Agent Operations Manual

## RULES (Non-Negotiable)

1. **DO NOT fabricate results.** Every number must come from actually running the backtest.
2. **DO NOT skip steps.** Follow the workflow exactly: browse → extract → save pine → convert → test → record → push.
3. **DO NOT take shortcuts.** If a conversion fails, debug it. Do not invent placeholder logic.
4. **DO NOT modify `scripts/` files** unless fixing a bug. Your job is to create files in `backtests/` and `pine_scripts/`.
5. **ALWAYS use `self.I()` wrapper** for indicators in the `init()` method. Never compute indicators outside of `self.I()`.
6. **ALWAYS run the backtest** using `python3 scripts/run_single_backtest.py backtests/<name>.py <TICKER>`.
7. **COMMIT every 5 indicators** processed (successful or failed).

---

## Phase 0: Setup Verification

Before starting, verify the environment:

```bash
cd /home/clavier/.openclaw/workspace/tradingview-backtest

# 1. Check dependencies
python3 -c "from backtesting import Backtest; import ta; import yfinance; print('Dependencies OK')"

# 2. Run example backtest
python3 scripts/run_single_backtest.py backtests/_example_rsi_bounce.py SPY

# 3. Check results were recorded
cat results/master_results.csv
```

If any step fails, fix it before proceeding.

---

## Phase 1: Browse TradingView Indicators

### Where to Browse

1. **Editor's Picks**: `https://www.tradingview.com/scripts/editors-picks/`
2. **Top Scripts**: `https://www.tradingview.com/scripts/`
3. **By Category**:
   - Trend: `https://www.tradingview.com/scripts/trend/`
   - Oscillators: `https://www.tradingview.com/scripts/oscillators/`
   - Volume: `https://www.tradingview.com/scripts/volume/`
   - Volatility: `https://www.tradingview.com/scripts/volatility/`

### Selection Criteria

Look for indicators that:
- Have **open source** Pine Script (source code visible)
- Generate **clear buy/sell signals** (not just overlays)
- Use **standard technical analysis** concepts (RSI, MACD, BB, etc.)
- Have **reasonable logic** that can be converted to entry/exit rules

Skip indicators that:
- Are drawing tools or labels only
- Require real-time data feeds
- Are purely visual (color bars, backgrounds)
- Need external data sources

---

## Phase 2: Extract Pine Script

For each indicator:

1. Navigate to the indicator page
2. Find and copy the full Pine Script source code
3. Save to `pine_scripts/<indicator_name>.pine`
4. Log to `logs/scrape_log.csv`:
   ```
   indicator_name,tradingview_url,pine_script_file,backtest_file,status,timestamp
   ```

---

## Phase 3: Convert Pine Script to Python Backtest

### Step-by-Step Conversion Process

1. **Copy the template**: `cp scripts/backtest_template.py backtests/<indicator_name>.py`
2. **Set INDICATOR_NAME**: Match the TradingView indicator name
3. **Convert indicators in `init()`**: Use `self.I()` wrapper + `ta` library
4. **Convert logic in `next()`**: Translate Pine Script conditions to Python
5. **Test**: Run with the runner script

### Pine Script → `ta` Library Mapping

| Pine Script | Python (`ta` library) |
|-------------|----------------------|
| `ta.rsi(close, 14)` | `ta.momentum.rsi(close, window=14)` |
| `ta.sma(close, 20)` | `ta.trend.sma_indicator(close, window=20)` |
| `ta.ema(close, 20)` | `ta.trend.ema_indicator(close, window=20)` |
| `ta.macd(close, 12, 26, 9)` | Use `ta.trend.macd_diff(close, window_slow=26, window_fast=12, window_sign=9)` |
| `ta.bb(close, 20, 2)` → upper | `ta.volatility.bollinger_hband(close, window=20, window_dev=2)` |
| `ta.bb(close, 20, 2)` → lower | `ta.volatility.bollinger_lband(close, window=20, window_dev=2)` |
| `ta.bb(close, 20, 2)` → middle | `ta.volatility.bollinger_mavg(close, window=20)` |
| `ta.atr(high, low, close, 14)` | `ta.volatility.average_true_range(high, low, close, window=14)` |
| `ta.stoch(high, low, close, 14, 3, 3)` %K | `ta.momentum.stoch(high, low, close, window=14, smooth_window=3)` |
| `ta.stoch(...)` %D | `ta.momentum.stoch_signal(high, low, close, window=14, smooth_window=3)` |
| `ta.adx(high, low, close, 14)` | `ta.trend.adx(high, low, close, window=14)` |
| `ta.cci(high, low, close, 20)` | `ta.trend.cci(high, low, close, window=20)` |
| `ta.obv(close, volume)` | `ta.volume.on_balance_volume(close, volume)` |
| `ta.wma(close, 20)` | `ta.trend.wma_indicator(close, window=20)` |
| `ta.willr(high, low, close, 14)` | `ta.momentum.williams_r(high, low, close, lbp=14)` |
| `ta.mfi(high, low, close, vol, 14)` | `ta.volume.money_flow_index(high, low, close, volume, window=14)` |
| `ta.change(x)` | Define: `lambda s: s.diff()` |
| `ta.crossover(a, b)` | In `next()`: `self.a[-2] <= self.b[-2] and self.a[-1] > self.b[-1]` |
| `ta.crossunder(a, b)` | In `next()`: `self.a[-2] >= self.b[-2] and self.a[-1] < self.b[-1]` |

### `self.I()` Rules and Common Pitfalls

**CORRECT usage:**
```python
def init(self):
    # Pass function + arguments to self.I()
    self.rsi = self.I(ta.momentum.rsi, pd.Series(self.data.Close), window=14)
    self.sma_20 = self.I(ta.trend.sma_indicator, pd.Series(self.data.Close), window=20)
    self.atr = self.I(ta.volatility.average_true_range,
                      pd.Series(self.data.High),
                      pd.Series(self.data.Low),
                      pd.Series(self.data.Close), window=14)
```

**WRONG — do NOT do this:**
```python
def init(self):
    # WRONG: computing outside self.I()
    rsi_values = ta.momentum.rsi(pd.Series(self.data.Close), window=14)
    self.rsi = rsi_values  # This will NOT work with backtesting.py
```

**For custom/complex indicators**, define a helper function:
```python
def calc_custom_indicator(close, high, low, window=14):
    """Helper that takes arrays/Series and returns array/Series."""
    rsi = ta.momentum.rsi(close, window=window)
    atr = ta.volatility.average_true_range(high, low, close, window=window)
    return rsi / atr  # example combination

class MyStrategy(Strategy):
    def init(self):
        self.custom = self.I(calc_custom_indicator,
                             pd.Series(self.data.Close),
                             pd.Series(self.data.High),
                             pd.Series(self.data.Low),
                             window=14)
```

**Key rules for `self.I()`:**
- First argument: a **callable** (function)
- Remaining arguments: the function's parameters
- The function must return a 1D array/Series of same length as data
- Wrap `self.data.Close` etc. in `pd.Series()` to ensure compatibility
- Use keyword arguments for named parameters

### Handling `next()` Logic

```python
def next(self):
    # Always check for NaN before using indicator values
    if pd.isna(self.rsi[-1]):
        return

    # Crossover detection (manual)
    crossed_above = self.fast_ma[-2] <= self.slow_ma[-2] and self.fast_ma[-1] > self.slow_ma[-1]
    crossed_below = self.fast_ma[-2] >= self.slow_ma[-2] and self.fast_ma[-1] < self.slow_ma[-1]

    # Position management
    if not self.position:
        if crossed_above:
            self.buy()
    elif self.position:
        if crossed_below:
            self.position.close()
```

---

## Phase 4: Run Backtest

```bash
# Run on SPY
python3 scripts/run_single_backtest.py backtests/<indicator_name>.py SPY

# Run on QQQ
python3 scripts/run_single_backtest.py backtests/<indicator_name>.py QQQ
```

Results are automatically appended to `results/master_results.csv`.

### Quality Check (for Discord notification)

After running, check if the result meets alpha thresholds:
- Return > 20%
- Max Drawdown > -30%
- Trades >= 20
- Win Rate > 45%
- Profit Factor > 1.3

If it passes, run Discord notification:
```bash
python3 scripts/discord_notify.py '<json_result>'
```

---

## Phase 5: Git Commit & Push

Every 5 indicators processed:

```bash
cd /home/clavier/.openclaw/workspace/tradingview-backtest
git add -A
git commit -m "Add backtests: <indicator1>, <indicator2>, ... | Results in master_results.csv"
git push origin main
```

---

## IMPORTANT: Skip Rule

**If a conversion fails after 2 attempts, SKIP IT and move to the next indicator.** Do not spend your entire context debugging one strategy. Log the failure to `logs/errors.log` and `logs/scrape_log.csv` with status `skipped`, then move on. There are hundreds of indicators — don't get stuck on one.

## Error Recovery

| Error | Fix |
|-------|-----|
| `self.I()` returns wrong shape | Make sure your function returns a 1D array of same length as data |
| `NaN` errors in `next()` | Add `if pd.isna(self.indicator[-1]): return` at the top |
| Module not found | Check imports: `import ta`, `from backtesting import Backtest, Strategy` |
| No trades generated | Review logic — conditions might be too restrictive, loosen thresholds |
| Timeout (120s) | Strategy may be too complex or data download failed — simplify or retry |
| yfinance download fails | Check internet, retry, or use cached data in `data_cache/` |

---

## File Reference

| File | Purpose |
|------|---------|
| `scripts/backtest_template.py` | Template — copy to create new backtests |
| `scripts/run_single_backtest.py` | Runner — executes backtest + records results |
| `scripts/discord_notify.py` | Notifier — sends Discord webhook for good strategies |
| `scripts/data_loader.py` | Data — downloads + caches yfinance data |
| `backtests/_example_rsi_bounce.py` | Example — reference for converting Pine Script |
| `results/master_results.csv` | Results — all backtest results aggregated |
| `logs/scrape_log.csv` | Progress — which indicators have been processed |
| `logs/errors.log` | Errors — failed backtests and reasons |
