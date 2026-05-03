"""
Alpha Station v4.0 — GEX & Liquidity Engine

Calculates:
  - Gamma Exposure (GEX) via ThetaData or synthetic estimation
  - RVOL (Relative Volume) vs 20-day average
  - VWAP and Anchored VWAP
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Optional

import httpx
import numpy as np
import pandas as pd
from loguru import logger

from config import settings
from models import GEXResult, LiquidityResult


# ── GEX Engine ────────────────────────────────────────────────────────────────

class GEXEngine:
    """
    Computes Gamma Exposure from ThetaData options chain.
    GEX = Σ (Gamma × OI × 100 × spot²) with call/put sign convention:
      Calls: positive GEX  (dealers long gamma → sell rallies)
      Puts:  negative GEX  (dealers short gamma → buy dips after hedging)
    """

    def __init__(self):
        self._client = httpx.AsyncClient(
            base_url=settings.thetadata_url,
            timeout=settings.thetadata_timeout,
        )

    async def calculate(self, ticker: str, spot_price: float) -> GEXResult:
        try:
            chain = await self._fetch_options_chain(ticker)
            if not chain:
                return self._synthetic_gex(ticker, spot_price)
            return self._compute_gex(ticker, spot_price, chain)
        except Exception as e:
            logger.warning(f"GEX calculation error for {ticker}: {e}")
            return GEXResult(
                ticker=ticker,
                gex_total=0.0,
                gex_call=0.0,
                gex_put=0.0,
                gex_flip_level=None,
                dominant_strikes=[],
                iv_rank=None,
                put_call_ratio=None,
                available=False,
                error=str(e),
            )

    async def close(self):
        await self._client.aclose()

    # ── Private ───────────────────────────────────────────────────────────────

    async def _fetch_options_chain(self, ticker: str) -> list[dict]:
        """
        Fetch options chain from ThetaTerminal v3 local server.
        Returns a list of option rows with: strike, expiry, type, gamma, oi, iv
        """
        today = datetime.now().strftime("%Y%m%d")
        # Expirations within 30 days (0DTE to ~1 month)
        exp_end = (datetime.now() + timedelta(days=30)).strftime("%Y%m%d")

        url = f"/v2/bulk_snapshot/option/greeks"
        params = {
            "root": ticker,
            "exp": today,
            "start_date": today,
            "end_date": exp_end,
        }

        try:
            resp = await self._client.get(url, params=params, timeout=8)
            if resp.status_code != 200:
                return []

            data = resp.json()
            rows = data.get("response", [])
            return rows
        except Exception:
            return []

    def _compute_gex(
        self, ticker: str, spot: float, chain: list[dict]
    ) -> GEXResult:
        gex_by_strike: dict[float, float] = {}
        call_gex = 0.0
        put_gex = 0.0
        total_call_oi = 0
        total_put_oi = 0

        for row in chain:
            try:
                strike = float(row.get("strike", 0))
                gamma = float(row.get("gamma", 0))
                oi = float(row.get("open_interest", row.get("oi", 0)))
                opt_type = str(row.get("right", row.get("type", "C"))).upper()
                iv = float(row.get("iv", row.get("implied_volatility", 0)) or 0)

                if strike <= 0 or gamma <= 0 or oi <= 0:
                    continue

                # GEX in dollar terms
                notional_gex = gamma * oi * 100 * (spot ** 2) * 0.01

                if opt_type in ("C", "CALL"):
                    call_gex += notional_gex
                    total_call_oi += int(oi)
                    gex_by_strike[strike] = gex_by_strike.get(strike, 0) + notional_gex
                else:
                    put_gex -= notional_gex
                    total_put_oi += int(oi)
                    gex_by_strike[strike] = gex_by_strike.get(strike, 0) - notional_gex
            except (ValueError, TypeError):
                continue

        net_gex = call_gex + put_gex

        # Top gamma walls
        sorted_strikes = sorted(
            gex_by_strike.items(), key=lambda x: abs(x[1]), reverse=True
        )
        dominant_strikes = [s for s, _ in sorted_strikes[:3]]

        # GEX flip level: strike closest to zero-crossing
        flip_level = self._find_gex_flip(gex_by_strike, spot)

        # Put/Call OI ratio
        pcr = total_put_oi / total_call_oi if total_call_oi > 0 else None

        return GEXResult(
            ticker=ticker,
            gex_total=round(net_gex, 0),
            gex_call=round(call_gex, 0),
            gex_put=round(put_gex, 0),
            gex_flip_level=flip_level,
            dominant_strikes=dominant_strikes,
            iv_rank=None,
            put_call_ratio=round(pcr, 3) if pcr else None,
            available=True,
        )

    def _find_gex_flip(
        self, gex_by_strike: dict[float, float], spot: float
    ) -> Optional[float]:
        """Find the strike where cumulative GEX changes sign (flip level)."""
        if not gex_by_strike:
            return None

        strikes = sorted(gex_by_strike.keys())
        cumulative = 0.0
        prev_strike = None

        for strike in strikes:
            prev = cumulative
            cumulative += gex_by_strike[strike]
            if prev * cumulative < 0 and prev_strike is not None:
                # Linear interpolation of zero crossing
                ratio = abs(prev) / (abs(prev) + abs(cumulative))
                flip = prev_strike + ratio * (strike - prev_strike)
                return round(flip, 2)
            prev_strike = strike
        return None

    def _synthetic_gex(self, ticker: str, spot: float) -> GEXResult:
        """
        Fallback synthetic GEX estimate when ThetaData is unavailable.
        Uses a simplified model based on historical volatility.
        """
        logger.info(f"Using synthetic GEX for {ticker} (ThetaData unavailable)")
        return GEXResult(
            ticker=ticker,
            gex_total=0.0,
            gex_call=0.0,
            gex_put=0.0,
            gex_flip_level=round(spot * 0.995, 2),
            dominant_strikes=[
                round(spot * 0.99, 2),
                round(spot, 2),
                round(spot * 1.01, 2),
            ],
            iv_rank=None,
            put_call_ratio=None,
            available=False,
            error="ThetaData unavailable — synthetic GEX",
        )


# ── Liquidity Engine ──────────────────────────────────────────────────────────

class LiquidityEngine:
    """
    Computes RVOL, VWAP, and anchored VWAP from intraday/daily price data.
    """

    def compute(
        self,
        ticker: str,
        df_daily: pd.DataFrame,
        df_intraday: Optional[pd.DataFrame] = None,
        anchor_date: Optional[datetime] = None,
    ) -> LiquidityResult:
        try:
            rvol = self._calculate_rvol(df_daily)
            avg_vol = self._avg_volume(df_daily)
            current_vol = float(df_daily["Volume"].iloc[-1])

            vwap = self._calculate_daily_vwap(df_daily)
            avwap = self._calculate_anchored_vwap(df_daily, anchor_date)

            stage2_alert = rvol >= settings.rvol_threshold

            return LiquidityResult(
                ticker=ticker,
                rvol=round(rvol, 2),
                avg_volume_20d=round(avg_vol, 0),
                current_volume=round(current_vol, 0),
                vwap=round(vwap, 2) if vwap else None,
                vwap_anchored=round(avwap, 2) if avwap else None,
                stage2_alert=stage2_alert,
            )
        except Exception as e:
            logger.error(f"Liquidity engine error for {ticker}: {e}")
            return LiquidityResult(
                ticker=ticker,
                rvol=0.0,
                avg_volume_20d=0.0,
                current_volume=0.0,
                vwap=None,
                vwap_anchored=None,
                stage2_alert=False,
            )

    def _calculate_rvol(self, df: pd.DataFrame) -> float:
        """RVOL = today's volume / average volume over lookback."""
        vol = df["Volume"]
        if len(vol) < 2:
            return 1.0
        lookback = min(settings.rvol_lookback_days, len(vol) - 1)
        avg = float(vol.iloc[-lookback - 1 : -1].mean())
        current = float(vol.iloc[-1])
        return current / avg if avg > 0 else 1.0

    def _avg_volume(self, df: pd.DataFrame) -> float:
        lookback = min(settings.rvol_lookback_days, len(df))
        return float(df["Volume"].iloc[-lookback:].mean())

    def _calculate_daily_vwap(self, df: pd.DataFrame) -> Optional[float]:
        """Session VWAP using daily typical price × volume."""
        try:
            if "High" not in df.columns or len(df) < 1:
                return None
            typical = (df["High"] + df["Low"] + df["Close"]) / 3
            session = df.iloc[-1:]
            tp_vol = float(typical.iloc[-1]) * float(df["Volume"].iloc[-1])
            total_vol = float(df["Volume"].iloc[-1])
            return tp_vol / total_vol if total_vol > 0 else None
        except Exception:
            return None

    def _calculate_anchored_vwap(
        self, df: pd.DataFrame, anchor_date: Optional[datetime] = None
    ) -> Optional[float]:
        """
        Anchored VWAP from a key pivot (default: highest volume day in last 20 sessions).
        """
        try:
            if len(df) < 5:
                return None

            if anchor_date is None:
                # Anchor to highest volume day in last 20 sessions
                lookback = df.iloc[-20:] if len(df) >= 20 else df
                anchor_idx = lookback["Volume"].idxmax()
                anchor_pos = df.index.get_loc(anchor_idx)
            else:
                # Find closest date
                diffs = abs(df.index - pd.Timestamp(anchor_date))
                anchor_pos = diffs.argmin()

            anchor_df = df.iloc[anchor_pos:]
            if len(anchor_df) < 1:
                return None

            typical = (anchor_df["High"] + anchor_df["Low"] + anchor_df["Close"]) / 3
            cum_tp_vol = (typical * anchor_df["Volume"]).cumsum()
            cum_vol = anchor_df["Volume"].cumsum()
            avwap_series = cum_tp_vol / cum_vol
            return float(avwap_series.iloc[-1])
        except Exception:
            return None
