# IV Mean Reversion

Implied Volatility mean-reversion research & backtesting framework using the **Interactive Brokers API** (`ib_insync`).

## Prerequisites
- Python **3.11**
- IB Gateway or TWS running locally (paper or live)

## Quick Start

```bash
# 1. Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies (editable package + requirements)
pip install -e .
pip install -r requirements.txt

# 3. Copy and edit environment variables
cp .env .env.local   # adjust IB_HOST / IB_PORT if needed

# 4. Download option chain data (IB Gateway must be running)
python scripts/download_iv.py --symbol SPY

# 5. Open the backtesting notebook
jupyter lab notebooks/01_iv_backtest.ipynb
```

## Project Structure

| Path | Purpose |
|------|---------|
| `src/iv_mr/ib_connector.py` | IB API connection & data helpers |
| `src/iv_mr/iv_utils.py` | IV storage, z-score, percentile, half-life |
| `scripts/download_iv.py` | CLI script to pull option chains |
| `notebooks/` | Jupyter notebooks for research & backtesting |
| `data/` | Parquet files (auto-created) |

## VS Code Integration
- **Run/Debug**: use the *Download IV (SPY)* launch configuration in `.vscode/launch.json`
- **Notebooks**: the kernel will pick up `src/` automatically via `PYTHONPATH`
- **Intellisense**: `src/` is added to `python.analysis.extraPaths`
