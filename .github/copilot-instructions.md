# IV Mean Reversion – Copilot Instructions

## Project Overview
This project downloads and analyses **Implied Volatility (IV)** data from Interactive Brokers (via `ib_insync`), stores it with `pyarrow`/Parquet, and provides a backtesting framework based on IV mean-reversion strategies using Jupyter notebooks.

## Stack
- **Python 3.11** (recommended for ib_insync + all listed packages)
- `ib_insync` — IB API async wrapper
- `pandas`, `numpy`, `scipy` — data wrangling & statistics
- `yfinance` — supplemental market data
- `matplotlib`, `seaborn` — visualisation
- `pyarrow` — Parquet I/O
- `jupyter` — interactive notebooks

## Folder Structure
```
IV_mean_reversion/
├── data/              # Raw & processed Parquet files
├── scripts/           # Standalone Python scripts (data download, utils)
├── notebooks/         # Jupyter notebooks for research & backtesting
├── src/               # Reusable modules (iv_utils, ib_connector, …)
├── tests/             # Unit tests
├── .github/           # Copilot instructions
├── .vscode/           # VS Code settings & launch configs
├── requirements.txt
├── setup.py
└── README.md
```

## Coding Conventions
- All data saved as `.parquet` under `data/`
- Scripts import from `src/` using the package installed in editable mode (`pip install -e .`)
- Notebooks live in `notebooks/` and import from `src/` the same way
- Environment variable `IB_HOST` (default `127.0.0.1`) and `IB_PORT` (default `7497`) control IB Gateway connection
