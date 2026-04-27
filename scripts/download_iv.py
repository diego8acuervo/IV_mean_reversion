"""
download_iv.py – Download implied volatility snapshots from Interactive Brokers.

Usage:
    python scripts/download_iv.py --symbol SPY --expiry 20240920

Environment variables:
    IB_HOST       IB Gateway / TWS host  (default: 127.0.0.1)
    IB_PORT       IB Gateway / TWS port  (default: 7497)
    IB_CLIENT_ID  Client ID              (default: 1)
"""

import argparse
import sys
from pathlib import Path

# Ensure src/ is importable when running as a plain script
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from iv_mr.ib_connector import connect, get_option_chain
from iv_mr.iv_utils import save_iv_snapshot


def parse_args():
    p = argparse.ArgumentParser(description="Download IV data from IB")
    p.add_argument("--symbol", default="SPY", help="Underlying symbol")
    p.add_argument("--exchange", default="SMART")
    p.add_argument("--currency", default="USD")
    return p.parse_args()


def main():
    args = parse_args()
    print(f"Connecting to IB Gateway for {args.symbol} …")
    ib = connect()

    chains = get_option_chain(ib, args.symbol, args.exchange, args.currency)

    rows = []
    for chain in chains:
        for expiry in chain.expirations:
            for strike in chain.strikes:
                rows.append(
                    {
                        "symbol": args.symbol,
                        "expiry": expiry,
                        "strike": strike,
                        "exchange": chain.exchange,
                    }
                )

    df = pd.DataFrame(rows)
    out = save_iv_snapshot(df, f"{args.symbol}_chain")
    print(f"Saved {len(df)} rows → {out}")
    ib.disconnect()


if __name__ == "__main__":
    main()
