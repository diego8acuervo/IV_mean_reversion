"""
IV Mean Reversion — Daily Live Runner
Run after market close: downloads fresh IV, scans universe, places limit orders.
"""

import pandas as pd
from pathlib import Path
from ib_insync import IB, Stock, LimitOrder
from ibkr_iv_downloader import connect, download_iv, download_price, DATA_DIR
from signal_engine import scan_universe, ENTRY_DISC, PROFIT_TARGET

UNIVERSE_FILE = Path(__file__).parent.parent / "references" / "russell1000.txt"
ORDER_QTY     = 100       # shares per trade (or use position sizing logic)
ACCOUNT       = ""        # leave empty for default


def refresh_data(tickers: list[str]):
    """Update IV+price for all tickers (full history refresh)."""
    from ibkr_iv_downloader import download_universe
    download_universe(tickers)


def place_orders(signals: pd.DataFrame):
    """Place limit buy orders for today's signals."""
    ib = connect(client_id=10)
    for _, sig in signals.iterrows():
        contract = Stock(sig["ticker"], "SMART", "USD")
        ib.qualifyContracts(contract)
        order = LimitOrder(
            action        = "BUY",
            totalQuantity = ORDER_QTY,
            lmtPrice      = round(sig["limit_entry"], 2),
            tif           = "DAY",
            account       = ACCOUNT or "",
        )
        trade = ib.placeOrder(contract, order)
        print(f"  ✅ {sig['ticker']} BUY {ORDER_QTY} @ {sig['limit_entry']:.2f} | PT {sig['profit_target']:.2f}")
    ib.disconnect()


def run_daily():
    """Full daily workflow: refresh → scan → show signals → optionally place orders."""
    if not UNIVERSE_FILE.exists():
        print(f"⚠ Universe file not found: {UNIVERSE_FILE}")
        print("  Create it with one ticker per line, or use the test universe.")
        return

    tickers = [t.strip() for t in UNIVERSE_FILE.read_text().splitlines() if t.strip()]
    print(f"Universe: {len(tickers)} tickers from {UNIVERSE_FILE.name}")

    print("\n1/3 Refreshing data...")
    refresh_data(tickers)

    print("\n2/3 Scanning for signals...")
    signals = scan_universe(DATA_DIR)

    if signals.empty:
        print("\n✅ No signals today.")
        return

    print(f"\n3/3 {len(signals)} signal(s) found:\n")
    print(signals.to_string(index=False))

    confirm = input("\n⚠ Place orders? [y/N]: ")
    if confirm.lower() == "y":
        place_orders(signals)
        print("\n✅ Orders placed.")
    else:
        print("Orders not placed.")


if __name__ == "__main__":
    run_daily()
