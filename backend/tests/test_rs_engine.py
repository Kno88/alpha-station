"""
Unit tests for RS Line Engine v5.0
Run with: py -m pytest tests/test_rs_engine.py -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import pytest

from modules.rs_engine import RSEngine
from models import RSLineResult


def _make_df(trend: str = "up", n: int = 252) -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    if trend == "up":
        price = 100 + np.cumsum(np.random.normal(0.15, 1, n))
    elif trend == "down":
        price = 200 - np.cumsum(np.abs(np.random.normal(0.15, 1, n)))
    else:
        price = 100 + np.random.normal(0, 1, n)
    price = np.abs(price) + 1
    return pd.DataFrame({
        "Open": price * 0.99, "High": price * 1.02,
        "Low": price * 0.98, "Close": price,
        "Volume": np.random.randint(1_000_000, 5_000_000, n).astype(float),
    }, index=dates)


def _make_spy(n: int = 252) -> pd.DataFrame:
    np.random.seed(99)
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    price = 400 + np.cumsum(np.random.normal(0.05, 1, n))
    price = np.abs(price)
    return pd.DataFrame({
        "Open": price * 0.99, "High": price * 1.01,
        "Low": price * 0.99, "Close": price,
        "Volume": np.random.randint(50_000_000, 100_000_000, n).astype(float),
    }, index=dates)


class TestRSEngine:
    engine = RSEngine()

    def test_compute_returns_result(self):
        result = self.engine.compute("TEST", _make_df("up"), _make_spy())
        assert isinstance(result, RSLineResult)
        assert result.ticker == "TEST"

    def test_rs_line_positive(self):
        result = self.engine.compute("TEST", _make_df("up"), _make_spy())
        assert result.rs_line > 0

    def test_rs_rating_in_range(self):
        result = self.engine.compute("TEST", _make_df("up"), _make_spy())
        assert 1 <= result.rs_rating <= 99

    def test_uptrend_has_higher_rs_than_downtrend(self):
        spy = _make_spy()
        up_result = self.engine.compute("UP", _make_df("up"), spy)
        down_result = self.engine.compute("DOWN", _make_df("down"), spy)
        assert up_result.rs_rating > down_result.rs_rating

    def test_slope_positive_for_uptrend(self):
        result = self.engine.compute("TEST", _make_df("up"), _make_spy())
        assert result.rs_line_slope > 0

    def test_rank_universe(self):
        spy = _make_spy()
        r1 = self.engine.compute("A", _make_df("up"), spy)
        r2 = self.engine.compute("B", _make_df("down"), spy)
        r3 = self.engine.compute("C", _make_df("flat"), spy)
        ranked = self.engine.rank_universe([r1, r2, r3])
        assert ranked[0].rs_rank == 1
        assert ranked[-1].rs_rank == 3

    def test_empty_df_returns_default(self):
        result = self.engine.compute("TEST", pd.DataFrame(), _make_spy())
        assert result.rs_rating == 50
        assert result.rs_line == 0.0

    def test_short_data_handles_gracefully(self):
        result = self.engine.compute("TEST", _make_df("up", 10), _make_spy(10))
        assert isinstance(result, RSLineResult)
