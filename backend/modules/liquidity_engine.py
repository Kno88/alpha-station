"""
Alpha Station v5.0 — Liquidity Engine

Calculates:
  - RVOL (Relative Volume) vs 20-day average
  - VWAP and Anchored VWAP
  - Up/Down Volume Ratio (institutional accumulation detection)
  - Volume Dry-Up (VCP precursor signal)
  - Pocket Pivot (institutional buy signal)
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from loguru import logger

from config import settings
from models import LiquidityResult


class LiquidityEngine:
    """
    Computes RVOL, VWAP, anchored VWAP, and institutional volume signals.

    v5.0 additions:
      - Up/Down Volume Ratio: >1.5 = institutional accumulation
      - Volume Dry-Up: Declining volume = VCP setup forming
      - Pocket Pivot: High-volume up day on declining volume base
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

            # ── v5.0: Volume Profile Analysis ─────────────────────────────────
            ud_ratio = self._up_down_volume_ratio(df_daily)
            vol_dryup = self._detect_volume_dryup(df_daily)
            pocket = self._detect_pocket_pivot(df_daily)
            ad_rating = self._calculate_ad_rating(df_daily)

            return LiquidityResult(
                ticker=ticker,
                rvol=round(rvol, 2),
                avg_volume_20d=round(avg_vol, 0),
                current_volume=round(current_vol, 0),
                vwap=round(vwap, 2) if vwap else None,
                vwap_anchored=round(avwap, 2) if avwap else None,
                stage2_alert=stage2_alert,
                up_down_volume_ratio=round(ud_ratio, 2),
                volume_dry_up=vol_dryup,
                pocket_pivot=pocket,
                ad_rating=ad_rating,
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
                ad_rating="C",
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

    # ── v5.0: Volume Profile Methods ────────────────────────────────────────

    def _up_down_volume_ratio(self, df: pd.DataFrame, lookback: int = 50) -> float:
        """
        Up/Down Volume Ratio over the lookback period.

        Up Volume = Volume on days where Close > Open (buyers in control)
        Down Volume = Volume on days where Close < Open (sellers in control)

        Ratio > 1.5 = Institutional accumulation (bullish)
        Ratio < 0.7 = Institutional distribution (bearish)
        """
        try:
            period = min(lookback, len(df))
            recent = df.iloc[-period:]

            up_days = recent[recent["Close"] > recent["Open"]]
            down_days = recent[recent["Close"] < recent["Open"]]

            up_vol = float(up_days["Volume"].sum()) if len(up_days) > 0 else 0.0
            down_vol = float(down_days["Volume"].sum()) if len(down_days) > 0 else 1.0

            return up_vol / down_vol if down_vol > 0 else 1.0
        except Exception:
            return 1.0

    def _calculate_ad_rating(self, df: pd.DataFrame, lookback: int = 65) -> str:
        """
        Accumulation/Distribution Rating (A to E) based on Up/Down volume ratio
        over the last 13 weeks (approx 65 trading days).
        A: > 1.5 (Heavy Accumulation)
        B: 1.1 - 1.5 (Moderate Accumulation)
        C: 0.9 - 1.1 (Neutral)
        D: 0.6 - 0.9 (Distribution)
        E: < 0.6 (Heavy Distribution)
        """
        ud_ratio = self._up_down_volume_ratio(df, lookback)
        if ud_ratio >= 1.5: return "A"
        if ud_ratio >= 1.1: return "B"
        if ud_ratio >= 0.9: return "C"
        if ud_ratio >= 0.6: return "D"
        return "E"

    def _detect_volume_dryup(self, df: pd.DataFrame) -> bool:
        """
        Detect volume dry-up (contraction) — VCP precursor.

        Volume in last 10 days < 60% of 50-day average = dry-up.
        This is the "quiet before the storm" in Minervini's language.
        """
        try:
            if len(df) < 50:
                return False

            avg_vol_50 = float(df["Volume"].iloc[-50:].mean())
            avg_vol_10 = float(df["Volume"].iloc[-10:].mean())

            return avg_vol_10 < avg_vol_50 * 0.6
        except Exception:
            return False

    def _detect_pocket_pivot(self, df: pd.DataFrame) -> bool:
        """
        Pocket Pivot detection (Gil Morales / Chris Kacher).

        A Pocket Pivot occurs when:
        1. Price closes UP on the day
        2. Volume on that day > max DOWN volume of prior 10 days
        3. Price is above the 50-day MA

        This signals institutional buying during a base or pullback.
        """
        try:
            if len(df) < 15:
                return False

            # Today's data
            today = df.iloc[-1]
            is_up_day = float(today["Close"]) > float(today["Open"])

            if not is_up_day:
                return False

            today_vol = float(today["Volume"])

            # Max down volume in prior 10 days
            prior_10 = df.iloc[-11:-1]
            down_days = prior_10[prior_10["Close"] < prior_10["Open"]]

            if len(down_days) == 0:
                return False

            max_down_vol = float(down_days["Volume"].max())

            # Price above 50-day MA
            ma50 = float(df["Close"].rolling(50).mean().iloc[-1]) if len(df) >= 50 else 0.0
            above_ma50 = float(today["Close"]) > ma50 if ma50 > 0 else False

            return today_vol > max_down_vol and above_ma50
        except Exception:
            return False
