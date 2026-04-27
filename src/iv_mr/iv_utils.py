"""IV utility functions: storage, stats, and mean-reversion helpers."""

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def save_iv_snapshot(df: pd.DataFrame, name: str) -> Path:
    """Save *df* as a Parquet file under data/<name>.parquet."""
    path = DATA_DIR / f"{name}.parquet"
    pq.write_table(pa.Table.from_pandas(df), path)
    return path


def load_iv_snapshot(name: str) -> pd.DataFrame:
    """Load a Parquet file from data/<name>.parquet."""
    path = DATA_DIR / f"{name}.parquet"
    return pq.read_table(path).to_pandas()


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------

def iv_zscore(series: pd.Series, window: int = 20) -> pd.Series:
    """Rolling z-score of IV vs its recent history."""
    mu = series.rolling(window).mean()
    sigma = series.rolling(window).std()
    return (series - mu) / sigma


def iv_percentile(series: pd.Series, window: int = 252) -> pd.Series:
    """Rolling IV percentile rank (0–100) over *window* periods."""
    return series.rolling(window).apply(
        lambda x: pd.Series(x).rank(pct=True).iloc[-1] * 100, raw=False
    )


def half_life(series: pd.Series) -> float:
    """Ornstein–Uhlenbeck half-life of mean reversion (in periods)."""
    lag = series.shift(1)
    delta = series - lag
    valid = pd.concat([lag, delta], axis=1).dropna()
    beta = np.polyfit(valid.iloc[:, 0], valid.iloc[:, 1], 1)[0]
    return -np.log(2) / beta if beta < 0 else float("nan")
