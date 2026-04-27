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
PORT        = 7496          # 7497=TWS paper | 7496=TWS live | 4002=GW paper
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