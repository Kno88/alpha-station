"""
Alpha Station v4.0 — Data Fetcher

Centralizes all price/OHLCV data retrieval via yfinance with in-process caching.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
import yfinance as yf
from cachetools import TTLCache
from loguru import logger

# Cache OHLCV data for 5 minutes to avoid hammering yfinance
_price_cache: TTLCache = TTLCache(maxsize=200, ttl=300)


def get_daily_ohlcv(ticker: str, days: int = 300) -> Optional[pd.DataFrame]:
    """Return daily OHLCV DataFrame for the given ticker. Returns None on failure."""
    cache_key = f"{ticker}:{days}"
    if cache_key in _price_cache:
        return _price_cache[cache_key]

    try:
        period = f"{days}d"
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if df is None or df.empty:
            logger.warning(f"No data returned for {ticker}")
            return None

        df.index = pd.to_datetime(df.index)

        # Flatten MultiIndex columns FIRST (yfinance ≥1.0 always returns MultiIndex)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.dropna(subset=["Close", "Volume"])

        _price_cache[cache_key] = df
        return df
    except Exception as e:
        logger.error(f"Data fetch error for {ticker}: {e}")
        return None


def get_spot_price(ticker: str) -> Optional[float]:
    """Fast current price lookup from yfinance fast_info."""
    try:
        t = yf.Ticker(ticker)
        fi = t.fast_info
        # fast_info is an object in yfinance ≥1.0, not a dict
        for attr in ("last_price", "regular_market_price", "lastPrice", "regularMarketPrice"):
            try:
                price = getattr(fi, attr, None)
                if price:
                    return float(price)
            except Exception:
                pass
        df = get_daily_ohlcv(ticker, days=5)
        return float(df["Close"].iloc[-1]) if df is not None and len(df) > 0 else None
    except Exception:
        return None
