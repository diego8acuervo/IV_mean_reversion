# IV Mean Reversion – Copilot Instructions

## Project Overview
Downloads **Implied Volatility (IV)** data from Interactive Brokers (via `ib_insync`), stores it as Parquet, and provides a full pipeline: download → signal → backtest → live execution.

## Stack & Environment
- **Python 3.11.9** via pyenv — venv at `.venv/` (always use `.venv/bin/python`)
- **Always activate before running**: `source .venv/bin/activate`
- **Never use** the global pyenv interpreter directly — packages are only in `.venv/`
- `ib_insync`, `pandas`, `numpy`, `scipy`, `yfinance`, `matplotlib`, `seaborn`, `pyarrow`, `jupyter`, `ruff`, `pytest`
- Lint: `ruff check src scripts tests` | Tests: `pytest -q`

## Folder Structure
```
IV_mean_reversion/
├── data/iv_raw/           # Parquet per ticker: columns [open,high,low,close,volume,iv_annual]
├── scripts/
│   ├── ibkr_iv_downloader.py  # Step 1: IB connect + historical IV+price download
│   ├── signal_engine.py       # Step 2: DIV signal computation + universe scan
│   ├── backtester.py          # Step 3: vectorized backtest with limit order simulation
│   ├── live_runner.py         # Step 4: daily scan + limit order placement
│   ├── test_download.py       # Test batch of 20 liquid names (runs steps 1+2)
│   └── download_iv.py         # Legacy single-symbol downloader (uses src/iv_mr)
├── src/iv_mr/
│   ├── ib_connector.py        # connect(), get_option_chain(), get_market_data()
│   └── iv_utils.py            # save/load parquet, iv_zscore(), iv_percentile(), half_life()
├── notebooks/
│   └── 01_iv_backtest.ipynb   # Research notebook (yfinance fallback if no IB data)
├── tests/test_iv_utils.py     # Pytest: zscore shape, percentile bounds, half_life type
├── references/
│   ├── russell1000.txt        # Universe file (one ticker per line)
│   └── strategy_config.yaml  # All strategy parameters (tunable)
├── .venv/                     # Python 3.11.9 virtual environment
├── .github/workflows/ci.yml   # GitHub Actions: ruff lint + pytest on push/PR to main
├── pyproject.toml             # ruff + pytest config (line-length=100, testpaths=tests)
├── requirements.txt
└── setup.py                   # editable install: pip install -e .
```

## IBKR Connection
- **Ports**: `7497`=TWS paper | `7496`=TWS live | `4002`=Gateway paper | `4001`=Gateway live
- Current config uses **7496** (live TWS) — set in `strategy_config.yaml` and `ibkr_iv_downloader.py`
- Test connection: `python scripts/ibkr_iv_downloader.py` (runs `connection_test()` → pulls SPY IV)
- Throttle: 0.6s sleep between requests (~50 req/10s IBKR limit)

## Key Script APIs
| Script | Main functions |
|--------|---------------|
| `ibkr_iv_downloader.py` | `connect()`, `download_iv(ib, ticker)`, `download_price(ib, ticker)`, `download_universe(tickers, save=True)`, `connection_test()` |
| `signal_engine.py` | `compute_signals(df)`, `scan_universe(data_dir)` → returns `DataFrame` sorted by `div` desc; returns empty DataFrame with correct columns if no signals |
| `backtester.py` | `backtest_ticker(df, ticker)`, `plot_results(...)` — use `fill_between` not `fill=True` for drawdown plot |
| `live_runner.py` | `refresh_data(tickers)`, `place_orders(signals)`, `run_daily()` |
| `src/iv_mr/iv_utils.py` | `iv_zscore(s, window=20)`, `iv_percentile(s, window=252)`, `half_life(s)` |

## Data Schema (`data/iv_raw/<TICKER>.parquet`)
```
index: date (DatetimeIndex)
columns: open, high, low, close, volume, iv_annual
```
- `iv_annual`: annualised IV as decimal (e.g. 0.25 = 25%)
- `iv_daily = iv_annual / sqrt(252)` — computed in `signal_engine.py`
- Signal column: `div = abs(daily_return) / iv_daily` (>1 = price moved more than 1σ)

## Strategy Parameters (`strategy_config.yaml`)
```yaml
filters:  min_avg_volume: 200000 | min_price: 20.0 | ma_period: 200 | min_daily_iv: 0.0055
signal:   below_prev_low: true | exceeds_div: true
execution: entry_discount_pct: 0.005 | profit_target_pct: 0.04 | max_hold_days: 7
sizing:   capital: 100000 | position_size_pct: 0.05 | max_concurrent_positions: 5
```

## Coding Conventions
- Scripts in `scripts/` add their own dir to `sys.path` and import sibling scripts directly
- `src/iv_mr` modules imported via editable install (`pip install -e .`)
- All data persisted as `.parquet` — never CSV for time-series
- `scan_universe()` must return an empty DataFrame with correct columns (not raise) when no signals

## Security & Repository Rules (STRICT)
- **NEVER** change the GitHub repository visibility to **public**
  - Do not run `gh repo create --public`, `gh repo edit --visibility public`, or any equivalent
  - If a feature requires a public repo, propose alternatives
- **NEVER** commit, push, stage, or upload `.env`, `.env.local`, or any secrets/credentials
  - Always confirm `.env*` is in `.gitignore` before any `git add` / `git commit`
- Never echo credentials, tokens, or account IDs in terminal output or chat

## Common Errors & Fixes
| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: ib_insync` | Activate venv: `source .venv/bin/activate` — packages only in `.venv/` |
| `ConnectionRefusedError` on port | TWS/Gateway not running, or wrong port in `strategy_config.yaml` |
| `fill=True` not valid on `Series.plot()` | Use `ax.fill_between(dd.index, dd.values, 0, ...)` instead |
| `sort_values` on empty DataFrame | `scan_universe()` must return empty DF with columns, not raise |
| `No module named 'iv_mr'` in scripts | `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))` |

## Workflow
```
1. python scripts/ibkr_iv_downloader.py     # test connection
2. python scripts/test_download.py          # download 20 liquid names (5Y IV+price)
3. python scripts/signal_engine.py          # scan for today's signals
4. python scripts/backtester.py             # backtest stored data
5. python scripts/live_runner.py            # daily live run (places orders)
```

## Skills & References
- [iv-mean-reversion skill](iv-mean.reversion.md) — full strategy spec with code templates
- [TWS API docs](https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/)
- [ib_insync docs](https://ib-insync.readthedocs.io/en/latest/)
- [pandas](https://pandas.pydata.org/docs/) | [numpy](https://numpy.org/doc/stable/) | [pyarrow](https://arrow.apache.org/docs/python/)
