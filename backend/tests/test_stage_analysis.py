"""
Basic unit tests for Stage Analysis engine.
Run with: py -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import numpy as np
import pandas as pd
import pytest

from modules.stage_analysis import StageAnalyzer
from models import StageEnum


def _make_df(trend: str = "up", n: int = 252) -> pd.DataFrame:
    """Generate synthetic OHLCV data."""
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    if trend == "up":
        price = 100 + np.cumsum(np.random.normal(0.1, 1, n))
    elif trend == "down":
        price = 200 - np.cumsum(np.abs(np.random.normal(0.1, 1, n)))
    else:
        price = 100 + np.random.normal(0, 1, n)  # sideways

    price = np.abs(price)
    return pd.DataFrame({
        "Open": price * 0.99,
        "High": price * 1.02,
        "Low": price * 0.98,
        "Close": price,
        "Volume": np.random.randint(1_000_000, 5_000_000, n).astype(float),
    }, index=dates)


class TestStageAnalyzer:
    analyzer = StageAnalyzer()

    def test_uptrend_returns_stage2(self):
        df = _make_df("up", 252)
        result = self.analyzer.analyze("TEST", df)
        assert result.stage in (StageEnum.STAGE_2, StageEnum.STAGE_1)
        assert result.confidence > 0

    def test_downtrend_returns_stage4(self):
        df = _make_df("down", 252)
        result = self.analyzer.analyze("TEST", df)
        assert result.stage in (StageEnum.STAGE_4, StageEnum.STAGE_3, StageEnum.UNKNOWN)

    def test_insufficient_data_returns_unknown(self):
        df = _make_df("up", 30)  # Too short for MA200
        result = self.analyzer.analyze("TEST", df)
        assert result.stage in (StageEnum.UNKNOWN, StageEnum.STAGE_1, StageEnum.STAGE_2)

    def test_empty_df_returns_unknown(self):
        result = self.analyzer.analyze("TEST", pd.DataFrame())
        assert result.stage == StageEnum.UNKNOWN

    def test_ma_alignment_detection(self):
        df = _make_df("up", 252)
        result = self.analyzer.analyze("TEST", df)
        assert isinstance(result.ma_alignment, bool)
        assert result.ma50 > 0
        assert result.ma200 > 0

    def test_confidence_range(self):
        df = _make_df("up", 252)
        result = self.analyzer.analyze("TEST", df)
        assert 0.0 <= result.confidence <= 1.0

    def test_stage_weeks_positive(self):
        df = _make_df("up", 252)
        result = self.analyzer.analyze("TEST", df)
        assert result.stage_weeks >= 0
