
"""
Step 1: Download a test batch of 20 liquid Russell 1000 names.
Run this after confirming connection_test() passes.
 
Usage from project root:
    cd iv-mean-reversion
    python scripts/test_download.py
"""
 
import sys
from pathlib import Path
 
# Ensure scripts dir is importable
sys.path.insert(0, str(Path(__file__).parent))
 
from ibkr_iv_downloader import download_universe, connection_test
 
# 20 liquid, optionable names spanning sectors
TEST_UNIVERSE = [
    # Tech
    "AAPL", "MSFT", "NVDA", "META",
    # Financials
    "JPM", "GS", "BAC",
    # Healthcare
    "UNH", "JNJ", "PFE",
    # Consumer
    "AMZN", "HD", "NKE",
    # Industrials
    "CAT", "DE", "BA",
    # Energy
    "XOM", "CVX",
    # Comms / Other
    "NFLX", "DIS",
]
 
 
def main():
    print("=" * 60)
    print("  IV Mean Reversion — Test Download")
    print("=" * 60)
    print(f"\nTickers: {', '.join(TEST_UNIVERSE)}")
    print(f"Count:   {len(TEST_UNIVERSE)}")
    print(f"Duration: 5 Y\n")
 
    # Verify connection first
    print("Testing connection...")
    conn_ok = connection_test()
    # treat failure only when connection_test explicitly returns False (some implementations print status and return None)
    if conn_ok is False:
        print("\n❌ Connection failed. Check TWS is running on port 7497.")
        return
 
    print(f"\n{'─'*60}")
    print("Starting download...\n")
 
    # download_universe does not accept a 'duration' keyword in the current implementation; omit it
    results = download_universe(TEST_UNIVERSE, save=True)
 
    if results:
        print(f"\n{'='*60}")
        print(f"  DOWNLOAD COMPLETE")
        print(f"{'='*60}")
        print(f"  Tickers downloaded: {len(results)}/{len(TEST_UNIVERSE)}")
 
        # Quick data quality check
        for ticker, df in results.items():
            iv_null_pct = df["iv_annual"].isna().mean() * 100
            print(f"  {ticker:5s}: {len(df):>5} bars | "
                  f"IV range [{df['iv_annual'].min():.3f}, {df['iv_annual'].max():.3f}] | "
                  f"IV nulls: {iv_null_pct:.1f}%")
 
        print(f"\n  Data saved to: {Path(__file__).parent.parent / 'data' / 'iv_raw'}")
        print(f"\n  Next step: python scripts/backtester.py")
    else:
        print("\n❌ No data downloaded. Check:")
        print("   - TWS market data subscriptions (need US equities + options)")
        print("   - API permissions in TWS → Global Configuration → API")
 
 
if __name__ == "__main__":
    main()