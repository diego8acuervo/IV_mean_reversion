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
    dd.plot(ax=axes[1], title="Drawdown (%)", color="firebrick", alpha=0.4)
    axes[1].fill_between(dd.index, dd.values, 0, color="firebrick", alpha=0.3)
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