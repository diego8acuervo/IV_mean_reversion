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

## Security & Repository Rules (STRICT)
- **NEVER** change the GitHub repository visibility to **public**. The repo must always remain **private**.
  - Do not run `gh repo create ... --public`, `gh repo edit ... --visibility public`, or any equivalent API call.
  - If a feature requires a public repo (e.g. free-tier branch protection), propose alternatives instead of changing visibility.
- **NEVER** commit, push, stage, or upload `.env`, `.env.local`, or any file containing secrets, API keys, tokens, or IB credentials.
  - Always confirm `.env*` patterns are present in `.gitignore` before any `git add` / `git commit`.
  - Never `git add .env` or `git add -f` on any secret file, even if requested implicitly.
- Treat all credentials, tokens, and account IDs as sensitive — never echo them in terminal output or chat.

## Skills
See also:
- [iv-mean-reversion](https://github.com/diego8acuervo/iv-mean-reversion.md)
- [tws_api_documentation](https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#api-introduction)
- [ib_insync](https://ib-insync.readthedocs.io/en/latest/)
- [pandas](https://pandas.pydata.org/docs/)
- [numpy](https://numpy.org/doc/stable/)
- [pyarrow](https://arrow.apache.org/docs/python/)
