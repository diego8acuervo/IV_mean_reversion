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
    if not signals:
        print("No signals found.")
        return pd.DataFrame(columns=["ticker", "div", "iv_daily", "close", "prev_low"])
    
    return pd.DataFrame(signals).sort_values("div", ascending=False)


if __name__ == "__main__":
    hits = scan_universe()
    print(f"\n{'='*60}")
    print(f"SIGNALS TODAY: {len(hits)}")
    print(hits.to_string(index=False))
