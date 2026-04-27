"""Smoke tests for iv_mr utilities."""

import numpy as np
import pandas as pd

from iv_mr.iv_utils import half_life, iv_percentile, iv_zscore


def _series():
    rng = np.random.default_rng(42)
    return pd.Series(20 + rng.standard_normal(300).cumsum() * 0.1)


def test_zscore_shape():
    s = _series()
    z = iv_zscore(s, window=20)
    assert len(z) == len(s)
    assert z.iloc[:19].isna().all()


def test_percentile_bounds():
    s = _series()
    p = iv_percentile(s, window=100).dropna()
    assert (p >= 0).all() and (p <= 100).all()


def test_half_life_returns_float():
    s = _series()
    hl = half_life(s)
    assert isinstance(hl, float)
