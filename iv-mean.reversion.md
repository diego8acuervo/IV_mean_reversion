---
name: iv-mean-reversion
description: |
  Implied Volatility Mean Reversion strategy for US equities (Russell 1000). Use this skill
  whenever the user wants to build, backtest, run, or extend a systematic long mean reversion
  strategy timed with implied volatility — including IBKR data download, signal generation,
  backtesting, and live execution scaffolding. Trigger on ANY mention of: IV mean reversion,
  implied volatility swing trading, IBKR IV download, daily implied volatility signals, IV-based
  entry/exit, or requests to replicate the CrackingMarkets / SystematicPeter strategy.
  Also trigger when the user asks to combine RSI mean reversion with IV filters, or wants to
  build a low-exposure equity strategy using options-derived data.
---

# IV Mean Reversion Skill

## Strategy Overview

Long-only mean reversion on Russell 1000 stocks timed with **daily implied volatility** (DIV).
The core insight: a price drop that exceeds the market's own expected daily move (as priced
in ATM options) is a high-quality mean reversion signal — not just oversold price action.

**Published performance (backtest 2020–2024, 243 trades):**
- CAGR ~22% | Max DD -5.12% | Win rate 74% | Avg capital exposure ~4.6%
- Compares to SPY: ~14% CAGR, -33.69% Max DD

Source: crackingmarkets.com/iv-mean-reversion (SystematicPeter)

---

## Workflow — Read This First

1. **Data download** → `scripts/ibkr_iv_downloader.py` — fetches IV + OHLCV from TWS/Gateway
2. **Signal generation** → `scripts/signal_engine.py` — computes DIV, filters, generates signals
3. **Backtest** → `scripts/backtester.py` — vectorized backtest with realistic fills
4. **Live runner** → `scripts/live_runner.py` — daily scan + limit order placement via IBKR API
5. **Config** → `references/strategy_config.yaml` — all parameters in one place

When the user asks to **build** the strategy: scaffold all scripts from templates below.
When the user asks to **connect to IBKR**: run the connection test in `scripts/ibkr_iv_downloader.py`.
When the user asks to **backtest**: run `scripts/backtester.py` with stored IV+price data.
When the user asks to **go live**: use `scripts/live_runner.py` scaffold.

---

## Step 0 — Prerequisites

```bash
pip install ib_insync pandas numpy scipy yfinance matplotlib seaborn pyarrow
```

TWS or IB Gateway must be running with:
- API enabled (TWS: Edit → Global Configuration → API → Settings)
- Socket port: **7497** (TWS paper), **7496** (TWS live), **4002** (Gateway paper), **4001** (Gateway live)
- "Allow connections from localhost only" checked (unless remote)
- Master Client ID: 0 (or match `CLIENT_ID` in config)

---

## Step 1 — IBKR IV Downloader

**File:** `scripts/ibkr_iv_downloader.py`

```python
"""
IBKR Implied Volatility + Price Downloader
Uses ib_insync to pull historical IV and OHLCV for a list of tickers.
Requires TWS or IB Gateway running and API enabled.
"""

import time
import pandas as pd
from pathlib import Path
from ib_insync import IB, Stock, util

# ── Config ────────────────────────────────────────────────────────────────────
HOST        = "127.0.0.1"
PORT        = 7497          # 7497=TWS paper | 7496=TWS live | 4002=GW paper
CLIENT_ID   = 1
DATA_DIR    = Path("data/iv_raw")
DURATION    = "5 Y"         # up to "10 Y" available from IBKR
BAR_SIZE    = "1 day"
SLEEP_SEC   = 0.6           # throttle: IBKR allows ~50 req/10s for historical
# ──────────────────────────────────────────────────────────────────────────────


def connect() -> IB:
    ib = IB()
    ib.connect(HOST, PORT, clientId=CLIENT_ID)
    print(f"Connected: {ib.isConnected()} | Account: {ib.managedAccounts()}")
    return ib


def download_iv(ib: IB, ticker: str) -> pd.DataFrame | None:
    """Download historical implied volatility (30-day ATM) for one ticker."""
    contract = Stock(ticker, "SMART", "USD")
    ib.qualifyContracts(contract)
    bars = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr=DURATION,
        barSizeSetting=BAR_SIZE,
        whatToShow="OPTION_IMPLIED_VOLATILITY",
        useRTH=True,
        formatDate=1,
    )
    if not bars:
        return None
    df = util.df(bars)[["date", "close"]].rename(columns={"close": "iv_annual"})
    df["date"] = pd.to_datetime(df["date"])
    df["ticker"] = ticker
    return df.set_index("date")


def download_price(ib: IB, ticker: str) -> pd.DataFrame | None:
    """Download OHLCV for one ticker."""
    contract = Stock(ticker, "SMART", "USD")
    ib.qualifyContracts(contract)
    bars = ib.reqHistoricalData(
        contract,
        endDateTime="",
        durationStr=DURATION,
        barSizeSetting=BAR_SIZE,
        whatToShow="TRADES",
        useRTH=True,
        formatDate=1,
    )
    if not bars:
        return None
    df = util.df(bars)[["date", "open", "high", "low", "close", "volume"]]
    df["date"] = pd.to_datetime(df["date"])
    df["ticker"] = ticker
    return df.set_index("date")


def download_universe(tickers: list[str], save: bool = True) -> dict[str, pd.DataFrame]:
    """Download IV + price for all tickers. Returns dict keyed by ticker."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    ib = connect()
    results = {}

    for i, ticker in enumerate(tickers):
        print(f"[{i+1}/{len(tickers)}] {ticker}...")
        try:
            iv_df    = download_iv(ib, ticker)
            price_df = download_price(ib, ticker)
            if iv_df is None or price_df is None:
                print(f"  ⚠ No data for {ticker}")
                continue
            merged = price_df.join(iv_df[["iv_annual"]], how="inner")
            results[ticker] = merged
            if save:
                merged.to_parquet(DATA_DIR / f"{ticker}.parquet")
            time.sleep(SLEEP_SEC)
        except Exception as e:
            print(f"  ✗ Error {ticker}: {e}")

    ib.disconnect()
    print(f"\nDone. Downloaded {len(results)}/{len(tickers)} tickers.")
    return results


def connection_test():
    """Quick connection test — call this first from VS Code."""
    ib = connect()
    # Pull 5 days of SPY IV as a sanity check
    test = download_iv(ib, "SPY")
    ib.disconnect()
    if test is not None:
        print("✅ Connection OK. Sample IV data:")
        print(test.tail())
    else:
        print("❌ Connected but got no data — check permissions.")


if __name__ == "__main__":
    connection_test()
```

**To test connection from VS Code terminal:**
```bash
python scripts/ibkr_iv_downloader.py
```

---

## Step 2 — Signal Engine

**File:** `scripts/signal_engine.py`

```python
"""
IV Mean Reversion Signal Engine
Computes daily IV, applies filters, generates entry signals.
"""

import numpy as np
import pandas as pd
from pathlib import Path

SQRT_252 = np.sqrt(252)

# ── Strategy Parameters (tune these) ─────────────────────────────────────────
MIN_VOLUME    = 200_000     # avg 20-day volume filter
MIN_PRICE     = 20.0        # minimum stock price
MA_PERIOD     = 200         # uptrend filter: close > MA(200)
MIN_DIV       = 0.0055      # minimum daily IV (0.55%) — filters low-vol stocks
ENTRY_DISC    = 0.005       # limit order discount below close (0.5% — tune this)
PROFIT_TARGET = 0.04        # 4% profit target from entry (tune this)
MAX_HOLD_DAYS = 7           # time-based stop: exit after N days if not filled
# ──────────────────────────────────────────────────────────────────────────────


def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Input: DataFrame with columns [open, high, low, close, volume, iv_annual]
           indexed by date, single ticker.
    Output: same DataFrame + signal columns.
    """
    df = df.copy()

    # Daily implied volatility
    df["div"] = df["iv_annual"] / SQRT_252

    # Daily price move (absolute %)
    df["daily_move"] = df["close"].pct_change().abs()

    # Uptrend filter
    df["ma200"] = df["close"].rolling(MA_PERIOD).mean()
    df["uptrend"] = df["close"] > df["ma200"]

    # Volume filter (20-day avg)
    df["avg_vol20"] = df["volume"].rolling(20).mean()

    # Condition 1: close below previous low
    df["below_prev_low"] = df["close"] < df["low"].shift(1)

    # Condition 2: daily move > daily IV (abnormal move)
    df["exceeds_div"] = df["daily_move"] > df["div"]

    # All filters
    df["entry_signal"] = (
        df["uptrend"]
        & (df["avg_vol20"] >= MIN_VOLUME)
        & (df["close"] >= MIN_PRICE)
        & (df["div"] >= MIN_DIV)
        & df["below_prev_low"]
        & df["exceeds_div"]
    )

    # Limit order price for next day
    df["limit_entry"] = df["close"] * (1 - ENTRY_DISC)

    # IV-based profit target: entry + profit_target
    # Extension idea: use IV to set dynamic PT (e.g., entry + N * div)
    df["profit_target"] = df["limit_entry"] * (1 + PROFIT_TARGET)

    return df


def scan_universe(data_dir: Path = Path("data/iv_raw")) -> pd.DataFrame:
    """Scan all parquet files, return today's signals."""
    signals = []
    for f in data_dir.glob("*.parquet"):
        ticker = f.stem
        df = pd.read_parquet(f)
        df = compute_signals(df)
        last = df.iloc[-1]
        if last["entry_signal"]:
            signals.append({
                "ticker":       ticker,
                "date":         df.index[-1],
                "close":        last["close"],
                "iv_annual":    last["iv_annual"],
                "div":          last["div"],
                "daily_move":   last["daily_move"],
                "limit_entry":  last["limit_entry"],
                "profit_target": last["profit_target"],
            })
    return pd.DataFrame(signals).sort_values("div", ascending=False)


if __name__ == "__main__":
    hits = scan_universe()
    print(f"\n{'='*60}")
    print(f"SIGNALS TODAY: {len(hits)}")
    print(hits.to_string(index=False))
```

---

## Step 3 — Backtester

**File:** `scripts/backtester.py`

```python
"""
IV Mean Reversion Backtester
Vectorized backtester with realistic limit order simulation.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from signal_engine import compute_signals, ENTRY_DISC, PROFIT_TARGET, MAX_HOLD_DAYS

# ── Backtest Config ───────────────────────────────────────────────────────────
DATA_DIR        = Path("data/iv_raw")
CAPITAL         = 100_000       # starting capital
POSITION_SIZE   = 0.05          # 5% of equity per trade (adjust for exposure target)
COMMISSION_PCT  = 0.001         # 0.1% per trade (round-trip: 0.2%)
START_DATE      = "2020-01-01"
# ──────────────────────────────────────────────────────────────────────────────


def backtest_ticker(df: pd.DataFrame, ticker: str) -> list[dict]:
    """Simulate trades for one ticker. Returns list of trade records."""
    df = compute_signals(df)
    trades = []

    i = 0
    while i < len(df) - 1:
        row = df.iloc[i]
        if not row["entry_signal"]:
            i += 1
            continue

        entry_limit = row["limit_entry"]
        target      = row["profit_target"]
        entry_date  = df.index[i]

        # Try to fill limit order over next MAX_HOLD_DAYS days
        filled      = False
        fill_price  = None
        fill_date   = None
        exit_price  = None
        exit_date   = None
        exit_reason = None

        for j in range(i + 1, min(i + 1 + MAX_HOLD_DAYS, len(df))):
            future = df.iloc[j]
            # Fill if low <= limit price
            if fill_price is None and future["low"] <= entry_limit:
                fill_price = min(entry_limit, future["open"])  # conservative
                fill_date  = df.index[j]
                filled     = True

            if filled:
                # Exit: hit profit target
                if future["high"] >= target:
                    exit_price  = target
                    exit_date   = df.index[j]
                    exit_reason = "target"
                    break
                # Exit: time stop (last allowed day)
                if j == min(i + MAX_HOLD_DAYS, len(df) - 1):
                    exit_price  = future["close"]
                    exit_date   = df.index[j]
                    exit_reason = "time_stop"
                    break

        if filled and exit_price:
            ret = (exit_price - fill_price) / fill_price
            ret_net = ret - 2 * COMMISSION_PCT
            trades.append({
                "ticker":       ticker,
                "entry_date":   fill_date,
                "exit_date":    exit_date,
                "entry_price":  fill_price,
                "exit_price":   exit_price,
                "return_gross": ret,
                "return_net":   ret_net,
                "exit_reason":  exit_reason,
                "iv_annual":    row["iv_annual"],
                "div":          row["div"],
            })
            i = df.index.get_loc(exit_date) + 1
        else:
            i += 1

    return trades


def run_backtest() -> pd.DataFrame:
    all_trades = []
    for f in DATA_DIR.glob("*.parquet"):
        ticker = f.stem
        df = pd.read_parquet(f)
        df = df[df.index >= START_DATE]
        if len(df) < 250:
            continue
        trades = backtest_ticker(df, ticker)
        all_trades.extend(trades)

    trades_df = pd.DataFrame(all_trades).sort_values("entry_date")
    return trades_df


def build_equity_curve(trades_df: pd.DataFrame) -> pd.Series:
    """Build daily equity curve from trade returns."""
    equity = CAPITAL
    curve  = []
    for _, t in trades_df.iterrows():
        pos_size = equity * POSITION_SIZE
        pnl      = pos_size * t["return_net"]
        equity  += pnl
        curve.append({"date": t["exit_date"], "equity": equity})
    return pd.DataFrame(curve).set_index("date")["equity"]


def print_stats(trades_df: pd.DataFrame, equity: pd.Series):
    wins    = (trades_df["return_net"] > 0).sum()
    total   = len(trades_df)
    wr      = wins / total if total else 0
    avg_ret = trades_df["return_net"].mean()
    years   = (trades_df["exit_date"].max() - trades_df["entry_date"].min()).days / 365
    cagr    = (equity.iloc[-1] / CAPITAL) ** (1 / years) - 1
    dd      = (equity / equity.cummax() - 1).min()

    # Sharpe (annualized daily returns)
    daily = equity.pct_change().dropna()
    sharpe = daily.mean() / daily.std() * np.sqrt(252)

    print(f"\n{'='*50}")
    print(f"BACKTEST RESULTS")
    print(f"{'='*50}")
    print(f"Trades:        {total}")
    print(f"Win rate:      {wr:.1%}")
    print(f"Avg return:    {avg_ret:.2%}")
    print(f"CAGR:          {cagr:.1%}")
    print(f"Max DD:        {dd:.1%}")
    print(f"Sharpe:        {sharpe:.2f}")
    print(f"Target exits:  {(trades_df['exit_reason']=='target').mean():.1%}")


def plot_results(equity: pd.Series):
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    equity.plot(ax=axes[0], title="Equity Curve — IV Mean Reversion", color="steelblue")
    axes[0].set_ylabel("Portfolio Value ($)")
    dd = (equity / equity.cummax() - 1) * 100
    dd.plot(ax=axes[1], title="Drawdown (%)", color="firebrick", fill=True, alpha=0.4)
    axes[1].set_ylabel("Drawdown (%)")
    plt.tight_layout()
    plt.savefig("backtest_results.png", dpi=150)
    plt.show()


if __name__ == "__main__":
    print("Running backtest...")
    trades = run_backtest()
    if trades.empty:
        print("No trades found — check data directory.")
    else:
        equity = build_equity_curve(trades)
        print_stats(trades, equity)
        plot_results(equity)
        trades.to_csv("backtest_trades.csv", index=False)
        print("\nTrades saved to backtest_trades.csv")
```

---

## Step 4 — Live Runner

**File:** `scripts/live_runner.py`

```python
"""
IV Mean Reversion — Daily Live Runner
Run after market close: downloads fresh IV, scans universe, places limit orders.
"""

import pandas as pd
from pathlib import Path
from ib_insync import IB, Stock, LimitOrder
from ibkr_iv_downloader import connect, download_iv, download_price
from signal_engine import scan_universe, compute_signals, ENTRY_DISC, PROFIT_TARGET

DATA_DIR    = Path("data/iv_raw")
UNIVERSE    = Path("references/russell1000.txt")   # one ticker per line
ACCOUNT     = ""        # leave empty to use default account
ORDER_QTY   = 100       # shares per trade (or use position sizing logic)


def refresh_data(tickers: list[str]):
    """Update last N days of IV+price for all tickers."""
    ib = connect()
    for ticker in tickers:
        try:
            iv_df    = download_iv(ib, ticker)
            price_df = download_price(ib, ticker)
            if iv_df is not None and price_df is not None:
                merged = price_df.join(iv_df[["iv_annual"]], how="inner")
                merged.to_parquet(DATA_DIR / f"{ticker}.parquet")
        except Exception as e:
            print(f"  ✗ {ticker}: {e}")
    ib.disconnect()


def place_orders(signals: pd.DataFrame):
    ib = connect()
    for _, sig in signals.iterrows():
        contract = Stock(sig["ticker"], "SMART", "USD")
        ib.qualifyContracts(contract)
        order = LimitOrder(
            action    = "BUY",
            totalQuantity = ORDER_QTY,
            lmtPrice  = round(sig["limit_entry"], 2),
            tif       = "DAY",           # day order — expires EOD if not filled
            account   = ACCOUNT or "",
        )
        trade = ib.placeOrder(contract, order)
        print(f"  ✅ {sig['ticker']} limit @ {sig['limit_entry']:.2f} | PT {sig['profit_target']:.2f}")
    ib.disconnect()


def run_daily():
    print("Loading universe...")
    tickers = UNIVERSE.read_text().strip().splitlines()

    print(f"Refreshing data for {len(tickers)} tickers...")
    refresh_data(tickers)

    print("Scanning for signals...")
    signals = scan_universe(DATA_DIR)

    if signals.empty:
        print("No signals today.")
        return

    print(f"\n{len(signals)} signal(s) found:")
    print(signals.to_string(index=False))

    confirm = input("\nPlace orders? [y/N]: ")
    if confirm.lower() == "y":
        place_orders(signals)
    else:
        print("Orders not placed.")


if __name__ == "__main__":
    run_daily()
```

---

## Key Parameters Reference

| Parameter | Default | Notes |
|---|---|---|
| `MIN_VOLUME` | 200,000 | 20-day avg daily volume |
| `MIN_PRICE` | $20 | Stock price floor |
| `MA_PERIOD` | 200 | Uptrend filter |
| `MIN_DIV` | 0.55% | Daily IV floor — filters low-vol names |
| `ENTRY_DISC` | 0.5% | Limit order below close (NOT published — tune) |
| `PROFIT_TARGET` | 4% | From entry (NOT published — tune) |
| `MAX_HOLD_DAYS` | 7 | Time stop in days (NOT published — tune) |
| `POSITION_SIZE` | 5% | Capital per trade |

> ⚠️ Parameters marked "NOT published" are inferred from similar RSI(2) strategies. Optimize via backtest on your data.

---

## Extension Ideas

- **IV-based exit**: Exit when current IV drops back below its 20-day median (mean reversion in IV itself)
- **IV percentile filter**: Only trade when stock IV rank > 50th percentile (elevated fear)
- **Short side**: Mirror logic with `close > prev_high` + `move > DIV` for short entries
- **Portfolio-level cap**: Max 5 concurrent positions (matches ~4.6% avg exposure)
- **Sector neutrality**: Avoid >2 names per GICS sector simultaneously

---

## Troubleshooting IBKR Connection

| Error | Fix |
|---|---|
| `ConnectionRefusedError` | TWS/Gateway not running or port mismatch |
| `No security definition found` | Stock not on SMART routing — try explicit exchange |
| `Historical data error 162` | Pacing violation — increase `SLEEP_SEC` |
| `No data returned` | Stock has no options (no IV) — skip ticker |
| `clientId already in use` | Change `CLIENT_ID` to unused number |

---

## Files Summary

```
iv-mean-reversion/
├── SKILL.md                     ← This file
├── scripts/
│   ├── ibkr_iv_downloader.py    ← IBKR connection + historical IV/price download
│   ├── signal_engine.py         ← DIV computation + entry signal logic
│   ├── backtester.py            ← Full vectorized backtest
│   └── live_runner.py           ← Daily scan + order placement
└── references/
    ├── strategy_config.yaml     ← Centralized parameter file
    └── russell1000.txt          ← Universe file (one ticker per line)
```