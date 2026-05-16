"""
Alpha Station v5.0 — Relative Strength (RS) Line Engine

THE #1 predictor of super-performing stocks (O'Neil, Minervini, Zanger).
RS Line = Stock Price / SPY Price (relative outperformance vs market).

Key signals:
  - RS Line New High BEFORE price new high → Super-performer setup
  - RS Rating ≥ 80 → Stock in top 20% of universe
  - RS Line above its 20-day MA → Short-term relative momentum
  - Bullish RS Divergence → RS making highs while price consolidates
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf
from cachetools import TTLCache
from loguru import logger

from config import settings
from models import RSLineResult

# Cache SPY data for 10 minutes
_spy_cache: TTLCache = TTLCache(maxsize=5, ttl=600)


def _get_spy_data(days: int = 300) -> Optional[pd.DataFrame]:
    """Fetch SPY benchmark data with caching."""
    cache_key = f"SPY:{days}"
    if cache_key in _spy_cache:
        return _spy_cache[cache_key]

    try:
        df = yf.download(settings.rs_benchmark, period=f"{days}d", progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None

        df.index = pd.to_datetime(df.index)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna(subset=["Close"])
        _spy_cache[cache_key] = df
        return df
    except Exception as e:
        logger.error(f"Failed to fetch SPY data: {e}")
        return None


class RSEngine:
    """
    Computes Relative Strength metrics for institutional stock selection.

    RS Line = Ticker Close / SPY Close (normalized ratio).
    RS Rating = Percentile rank of RS performance vs universe (1-99, IBD style).

    Usage:
        engine = RSEngine()
        result = engine.compute("NVDA", nvda_df, spy_df)
        rankings = engine.rank_universe(["NVDA", "SMCI", "AXON", ...])
    """

    def compute(
        self,
        ticker: str,
        df_ticker: pd.DataFrame,
        df_spy: Optional[pd.DataFrame] = None,
    ) -> RSLineResult:
        """Compute RS Line metrics for a single ticker."""
        try:
            # Get SPY data
            if df_spy is None:
                df_spy = _get_spy_data(days=max(300, settings.rs_lookback_days + 30))

            if df_spy is None or df_spy.empty:
                logger.warning(f"No SPY data for RS calculation of {ticker}")
                return self._default_result(ticker)

            # Align dates
            ticker_close = df_ticker["Close"].copy()
            spy_close = df_spy["Close"].copy()

            # Find common dates
            common_idx = ticker_close.index.intersection(spy_close.index)
            if len(common_idx) < 20:
                logger.warning(f"Insufficient overlapping data for RS: {ticker} ({len(common_idx)} days)")
                return self._default_result(ticker)

            ticker_aligned = ticker_close.loc[common_idx].astype(float)
            spy_aligned = spy_close.loc[common_idx].astype(float)

            # ── RS Line calculation ──────────────────────────────────────────
            rs_line = ticker_aligned / spy_aligned
            rs_current = float(rs_line.iloc[-1])

            # ── RS Line 20-day MA ────────────────────────────────────────────
            rs_ma20 = float(rs_line.rolling(20).mean().iloc[-1]) if len(rs_line) >= 20 else rs_current
            rs_above_ma = rs_current > rs_ma20

            # ── RS Line slope (20-day linear regression slope) ───────────────
            rs_slope = self._compute_slope(rs_line, window=20)

            # ── RS Line New High detection ───────────────────────────────────
            lookback = min(settings.rs_new_high_lookback, len(rs_line))
            rs_max = float(rs_line.iloc[-lookback:].max())

            rs_new_high = rs_current >= rs_max * 0.998  # Within 0.2% = new high
            rs_near_high = rs_current >= rs_max * (1 - settings.rs_near_high_pct)

            # ── Bullish RS Divergence ────────────────────────────────────────
            # RS at/near new high but price NOT at new high
            price_current = float(ticker_aligned.iloc[-1])
            price_max = float(ticker_aligned.iloc[-lookback:].max())
            price_at_high = price_current >= price_max * 0.95  # Within 5%
            rs_divergence_bullish = rs_near_high and not price_at_high

            # ── RS Rating (IBD-style 1-99 percentile) ────────────────────────
            # Composite of multi-timeframe RS performance
            rs_rating = self._compute_rs_rating(ticker_aligned, spy_aligned)

            # ── Multi-timeframe percentiles ──────────────────────────────────
            pct_63d = self._rs_change_percentile(ticker_aligned, spy_aligned, 63)
            pct_126d = self._rs_change_percentile(ticker_aligned, spy_aligned, 126)
            pct_252d = self._rs_change_percentile(ticker_aligned, spy_aligned, 252)

            return RSLineResult(
                ticker=ticker,
                rs_line=round(rs_current, 6),
                rs_rating=rs_rating,
                rs_line_new_high=rs_new_high,
                rs_line_near_high=rs_near_high,
                rs_line_slope=round(rs_slope, 6),
                rs_line_ma20=round(rs_ma20, 6),
                rs_line_above_ma=rs_above_ma,
                rs_divergence_bullish=rs_divergence_bullish,
                rs_rank=0,  # Set later by rank_universe()
                rs_percentile_63d=round(pct_63d, 1),
                rs_percentile_126d=round(pct_126d, 1),
                rs_percentile_252d=round(pct_252d, 1),
            )

        except Exception as e:
            logger.error(f"RS engine error for {ticker}: {e}")
            return self._default_result(ticker)

    def rank_universe(
        self,
        results: list[RSLineResult],
    ) -> list[RSLineResult]:
        """
        Rank a list of RS results by RS Rating (descending).
        Updates rs_rank field for each result.
        """
        sorted_results = sorted(results, key=lambda r: r.rs_rating, reverse=True)
        for i, result in enumerate(sorted_results):
            result.rs_rank = i + 1
        return sorted_results

    # ── Private helpers ──────────────────────────────────────────────────────

    def _compute_slope(self, series: pd.Series, window: int = 20) -> float:
        """Linear regression slope of the RS Line over the window."""
        try:
            data = series.iloc[-window:].dropna()
            if len(data) < window // 2:
                return 0.0

            x = np.arange(len(data), dtype=float)
            y = data.values.astype(float)

            # Normalize to avoid numerical issues
            y_mean = np.mean(y)
            if y_mean == 0:
                return 0.0
            y_norm = y / y_mean

            # Linear regression
            x_mean = np.mean(x)
            slope = np.sum((x - x_mean) * (y_norm - np.mean(y_norm))) / np.sum((x - x_mean) ** 2)
            return float(slope)
        except Exception:
            return 0.0

    def _compute_rs_rating(self, ticker_close: pd.Series, spy_close: pd.Series) -> int:
        """
        IBD-style RS Rating (1-99):
        Weighted composite of relative performance over multiple timeframes.
        Weight: 40% quarterly + 20% semi-annual + 20% annual + 20% recent 1-month
        """
        try:
            # Calculate relative performance over periods
            periods = {
                "1m": 21,
                "3m": 63,
                "6m": 126,
                "12m": 252,
            }

            scores = {}
            for label, days in periods.items():
                if len(ticker_close) > days and len(spy_close) > days:
                    ticker_ret = (float(ticker_close.iloc[-1]) / float(ticker_close.iloc[-days]) - 1)
                    spy_ret = (float(spy_close.iloc[-1]) / float(spy_close.iloc[-days]) - 1)
                    # Relative performance = outperformance vs SPY
                    scores[label] = ticker_ret - spy_ret
                else:
                    scores[label] = 0.0

            # Weighted composite
            composite = (
                scores.get("3m", 0) * 0.40
                + scores.get("6m", 0) * 0.20
                + scores.get("12m", 0) * 0.20
                + scores.get("1m", 0) * 0.20
            )

            # Map to 1-99 scale using sigmoid-like transformation
            # Composite of 0 = 50 (average), positive = above 50, negative = below 50
            import math
            rating = int(50 + 49 * math.tanh(composite * 3))
            return max(1, min(99, rating))

        except Exception:
            return 50

    def _rs_change_percentile(
        self, ticker_close: pd.Series, spy_close: pd.Series, days: int
    ) -> float:
        """Calculate the RS change over N days as a percentile score."""
        try:
            if len(ticker_close) <= days or len(spy_close) <= days:
                return 50.0

            ticker_ret = float(ticker_close.iloc[-1]) / float(ticker_close.iloc[-days]) - 1
            spy_ret = float(spy_close.iloc[-1]) / float(spy_close.iloc[-days]) - 1
            relative_perf = ticker_ret - spy_ret

            # Map to 0-100 percentile
            import math
            percentile = 50 + 49 * math.tanh(relative_perf * 4)
            return max(0.0, min(100.0, percentile))
        except Exception:
            return 50.0

    def _default_result(self, ticker: str) -> RSLineResult:
        """Return default RS result when calculation fails."""
        return RSLineResult(
            ticker=ticker,
            rs_line=0.0,
            rs_rating=50,
            rs_line_new_high=False,
            rs_line_near_high=False,
            rs_line_slope=0.0,
            rs_line_ma20=0.0,
            rs_line_above_ma=False,
            rs_divergence_bullish=False,
            rs_rank=0,
            rs_percentile_63d=50.0,
            rs_percentile_126d=50.0,
            rs_percentile_252d=50.0,
        )
