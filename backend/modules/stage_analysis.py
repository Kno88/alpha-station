"""
Alpha Station v5.0 — Stage Analysis Engine
Implements Weinstein Stage Method with Minervini trend template refinements.

Stage definitions:
  Stage 1: Basing — price flat/choppy around 30-week MA, volume contracting
  Stage 2: Advancing — price above all MAs, MAs aligned upward, expanding volume
  Stage 3: Topping — price stalling, MAs flattening/crossing
  Stage 4: Declining — price below all MAs, MAs declining

v5.0 additions:
  - VCP (Volatility Contraction Pattern) detection
  - Base Count tracking (1st base = most powerful)
  - Base Depth measurement (< 35% = healthy)
  - 52-week high/low tracking
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

from models import StageEnum, StageResult
from config import settings


class StageAnalyzer:
    """Detects Weinstein/Minervini stages from OHLCV price history."""

    # ── Minervini Trend Template thresholds ──────────────────────────────────
    MIN_PRICE_ABOVE_MA200_PCT = 0.0       # Price must be above 200-day MA
    MA50_ABOVE_MA150_REQUIRED = True
    MA150_ABOVE_MA200_REQUIRED = True
    MA200_TRENDING_UP_WEEKS = 1           # MA200 must be rising for N weeks
    PRICE_WITHIN_25PCT_52W_HIGH = True    # Price within 25% of 52-week high
    PRICE_25PCT_ABOVE_52W_LOW = True      # Price at least 25% above 52-week low

    def analyze(self, ticker: str, df: pd.DataFrame) -> StageResult:
        """
        df must have columns: Open, High, Low, Close, Volume
        with a DatetimeIndex, at least 252 rows for full accuracy.
        """
        if df is None or len(df) < 60:
            return self._unknown_result(ticker, "Insufficient price history")

        df = df.copy().sort_index()
        close = df["Close"]
        volume = df["Volume"]

        # ── Moving averages ──────────────────────────────────────────────────
        ma50 = close.rolling(settings.ma_short).mean()
        ma150 = close.rolling(settings.ma_mid).mean()
        ma200 = close.rolling(settings.ma_long).mean()

        price = float(close.iloc[-1])
        ma50_val = float(ma50.iloc[-1])
        ma150_val = float(ma150.iloc[-1]) if len(df) >= settings.ma_mid else float("nan")
        ma200_val = float(ma200.iloc[-1]) if len(df) >= settings.ma_long else float("nan")

        # If we don't have enough history for longer MAs, degrade gracefully
        has_ma150 = not np.isnan(ma150_val)
        has_ma200 = not np.isnan(ma200_val)

        # ── MA alignment checks (Minervini trend template) ───────────────────
        ma_aligned = (
            has_ma150
            and has_ma200
            and ma50_val > ma150_val
            and ma150_val > ma200_val
        )

        price_above_ma50 = price > ma50_val
        price_above_ma150 = has_ma150 and price > ma150_val
        price_above_ma200 = has_ma200 and price > ma200_val
        price_above_all = price_above_ma50 and price_above_ma150 and price_above_ma200

        # ── MA200 slope (trending up?) ────────────────────────────────────────
        ma200_trending_up = False
        if has_ma200 and len(ma200.dropna()) >= 10:
            ma200_1mo_ago = float(ma200.dropna().iloc[-21]) if len(ma200.dropna()) >= 21 else float("nan")
            if not np.isnan(ma200_1mo_ago):
                ma200_trending_up = ma200_val > ma200_1mo_ago

        # ── 52-week high/low ──────────────────────────────────────────────────
        lookback = min(252, len(close))
        high_52w = float(close.iloc[-lookback:].max())
        low_52w = float(close.iloc[-lookback:].min())

        within_25pct_high = price >= high_52w * 0.75
        above_25pct_low = price >= low_52w * 1.25

        # ── Volume analysis ──────────────────────────────────────────────────
        vol_10d = float(volume.iloc[-10:].mean())
        vol_50d = float(volume.iloc[-50:].mean()) if len(volume) >= 50 else vol_10d
        vol_expansion = vol_10d > vol_50d * 1.1   # Recent volume above average

        # ── Determine stage ──────────────────────────────────────────────────
        stage, confidence, notes = self._classify_stage(
            price=price,
            ma50=ma50_val,
            ma150=ma150_val if has_ma150 else None,
            ma200=ma200_val if has_ma200 else None,
            ma_aligned=ma_aligned,
            price_above_all=price_above_all,
            price_above_ma200=price_above_ma200,
            ma200_trending_up=ma200_trending_up,
            vol_expansion=vol_expansion,
            within_25pct_high=within_25pct_high,
            above_25pct_low=above_25pct_low,
        )

        # ── Detect Stage 1→2 transition ──────────────────────────────────────
        transitioning = self._detect_stage2_transition(
            close=close,
            ma50=ma50,
            ma150=ma150,
            ma200=ma200,
            volume=volume,
        )

        # ── Count weeks in current stage ─────────────────────────────────────
        stage_weeks = self._count_stage_weeks(close, ma50, ma200, stage)

        # ── Price vs MA200 % ─────────────────────────────────────────────────
        price_vs_ma200_pct = ((price - ma200_val) / ma200_val * 100) if has_ma200 else 0.0

        # ── 52-week high/low (already computed in _classify_stage context) ────
        lookback_52w = min(252, len(close))
        high_52w_val = float(close.iloc[-lookback_52w:].max())
        low_52w_val = float(close.iloc[-lookback_52w:].min())

        # ── VCP & Base Analysis (v5.0) ──────────────────────────────────
        vcp_detected, vcp_tightness = self._detect_vcp(close, volume)
        base_count = self._count_bases(close, ma50)
        base_depth = self._base_depth(close, lookback=60)

        return StageResult(
            stage=stage,
            confidence=round(confidence, 3),
            ma50=round(ma50_val, 2),
            ma150=round(ma150_val, 2) if has_ma150 else 0.0,
            ma200=round(ma200_val, 2) if has_ma200 else 0.0,
            price=round(price, 2),
            price_vs_ma200_pct=round(price_vs_ma200_pct, 2),
            ma_alignment=ma_aligned,
            price_above_all_mas=price_above_all,
            transitioning_to_2=transitioning,
            stage_weeks=stage_weeks,
            vcp_detected=vcp_detected,
            vcp_tightness=round(vcp_tightness, 3),
            base_count=base_count,
            base_depth_pct=round(base_depth, 2),
            high_52w=round(high_52w_val, 2),
            low_52w=round(low_52w_val, 2),
            notes=notes,
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _classify_stage(
        self,
        price: float,
        ma50: float,
        ma150: float | None,
        ma200: float | None,
        ma_aligned: bool,
        price_above_all: bool,
        price_above_ma200: bool,
        ma200_trending_up: bool,
        vol_expansion: bool,
        within_25pct_high: bool,
        above_25pct_low: bool,
    ) -> tuple[StageEnum, float, list[str]]:

        notes: list[str] = []
        score = 0.0
        max_score = 7.0

        # ── Stage 2 scoring (most bullish) ────────────────────────────────────
        s2_score = 0.0
        if ma_aligned:
            s2_score += 2.0
            notes.append("✅ MAs perfectly aligned (50>150>200)")
        if price_above_all:
            s2_score += 2.0
            notes.append("✅ Price above all MAs")
        if ma200_trending_up:
            s2_score += 1.0
            notes.append("✅ MA200 trending up")
        if vol_expansion:
            s2_score += 1.0
            notes.append("✅ Volume expanding")
        if within_25pct_high:
            s2_score += 0.5
        if above_25pct_low:
            s2_score += 0.5

        if s2_score >= 5.0:
            return StageEnum.STAGE_2, s2_score / 7.0, notes

        # ── Stage 4 (decline) ─────────────────────────────────────────────────
        if ma150 is not None and ma200 is not None:
            mas_inverted = ma50 < ma150 and ma150 < ma200
            price_below_all = price < ma50 and price < (ma150 or ma50) and price < (ma200 or ma50)
            if mas_inverted and price_below_all:
                notes.append("❌ MAs inverted, price below all MAs — Stage 4 decline")
                return StageEnum.STAGE_4, 0.75, notes

        # ── Stage 3 (topping) ─────────────────────────────────────────────────
        if ma200 is not None and price_above_ma200:
            if not ma_aligned:
                notes.append("⚠️ MAs losing alignment — Stage 3 distribution")
                return StageEnum.STAGE_3, 0.60, notes

        # ── Stage 1 (basing) ─────────────────────────────────────────────────
        if ma200 is not None:
            flat_band = abs(price - ma200) / ma200 < 0.10  # within 10% of MA200
            if flat_band:
                notes.append("📊 Price in tight range around MA200 — Stage 1 base")
                return StageEnum.STAGE_1, 0.65, notes

        notes.append("⚪ Inconclusive stage signals")
        return StageEnum.UNKNOWN, 0.3, notes

    def _detect_stage2_transition(
        self,
        close: pd.Series,
        ma50: pd.Series,
        ma150: pd.Series,
        ma200: pd.Series,
        volume: pd.Series,
    ) -> bool:
        """Detect if price is transitioning from Stage 1 to Stage 2."""
        try:
            if len(close) < 30:
                return False

            # Look back 10 days for transition: was in Stage 1, now breaking out
            recent_close = close.iloc[-10:]
            recent_ma50 = ma50.iloc[-10:]
            recent_vol = volume.iloc[-10:]
            avg_vol_50 = float(volume.iloc[-50:].mean()) if len(volume) >= 50 else float(volume.mean())

            # Price crossed above MA50 recently
            cross_above_ma50 = any(
                recent_close.iloc[i] > recent_ma50.iloc[i]
                and recent_close.iloc[i - 1] <= recent_ma50.iloc[i - 1]
                for i in range(1, len(recent_close))
            )

            # Volume surge on breakout
            vol_surge = float(recent_vol.iloc[-3:].mean()) > avg_vol_50 * 1.5

            # MA50 starting to slope up
            ma50_slope = float(recent_ma50.iloc[-1]) > float(recent_ma50.iloc[-5]) if len(recent_ma50) >= 5 else False

            return cross_above_ma50 and (vol_surge or ma50_slope)
        except Exception:
            return False

    def _count_stage_weeks(
        self,
        close: pd.Series,
        ma50: pd.Series,
        ma200: pd.Series,
        current_stage: StageEnum,
    ) -> int:
        """Estimate how many weeks the ticker has been in the current stage."""
        try:
            is_stage2 = close > ma50
            if current_stage == StageEnum.STAGE_2:
                condition = is_stage2
            elif current_stage == StageEnum.STAGE_4:
                condition = close < ma200
            else:
                condition = ~is_stage2

            count = 0
            for val in reversed(condition.values):
                if val:
                    count += 1
                else:
                    break
            return max(1, count // 5)  # convert trading days → weeks
        except Exception:
            return 0

    def _unknown_result(self, ticker: str, reason: str) -> StageResult:
        logger.warning(f"Stage analysis failed for {ticker}: {reason}")
        return StageResult(
            stage=StageEnum.UNKNOWN,
            confidence=0.0,
            ma50=0.0,
            ma150=0.0,
            ma200=0.0,
            price=0.0,
            price_vs_ma200_pct=0.0,
            ma_alignment=False,
            price_above_all_mas=False,
            transitioning_to_2=False,
            stage_weeks=0,
            vcp_detected=False,
            vcp_tightness=0.0,
            base_count=0,
            base_depth_pct=0.0,
            high_52w=0.0,
            low_52w=0.0,
            notes=[f"Error: {reason}"],
        )

    # ── VCP & Base Analysis (v5.0) ─────────────────────────────────────────────

    def _detect_vcp(self, close: pd.Series, volume: pd.Series) -> tuple[bool, float]:
        """
        Volatility Contraction Pattern (Minervini's favorite setup).

        VCP = Series of price contractions getting progressively tighter.
        Example: -25%, then -15%, then -8%, then -4% → Breakout!

        Returns (is_vcp, tightness_score).
        tightness_score: 0-1, where 1 = perfect contraction pattern.
        """
        try:
            if len(close) < 40:
                return False, 0.0

            # Look at last 60 days for VCP pattern
            recent = close.iloc[-60:].values.astype(float)
            recent_vol = volume.iloc[-60:].values.astype(float)

            # Find local peaks and troughs
            swings = []
            window = 5
            for i in range(window, len(recent) - window):
                # Local high
                if recent[i] == max(recent[i-window:i+window+1]):
                    swings.append(("H", i, recent[i]))
                # Local low
                elif recent[i] == min(recent[i-window:i+window+1]):
                    swings.append(("L", i, recent[i]))

            if len(swings) < 4:
                return False, 0.0

            # Calculate successive contraction depths
            contractions = []
            for j in range(len(swings) - 1):
                if swings[j][0] == "H" and swings[j+1][0] == "L":
                    depth = (swings[j][2] - swings[j+1][2]) / swings[j][2]
                    contractions.append(depth)

            if len(contractions) < 2:
                return False, 0.0

            # VCP = each contraction is smaller than the previous
            is_contracting = all(
                contractions[i] > contractions[i+1]
                for i in range(len(contractions) - 1)
            )

            # Volume should also be declining (dry-up)
            vol_first_half = float(np.mean(recent_vol[:30]))
            vol_second_half = float(np.mean(recent_vol[30:]))
            vol_declining = vol_second_half < vol_first_half * 0.8

            # Tightness = ratio of last contraction to first
            if contractions[0] > 0:
                tightness = 1.0 - (contractions[-1] / contractions[0])
            else:
                tightness = 0.0
            tightness = max(0.0, min(1.0, tightness))

            is_vcp = is_contracting and vol_declining and tightness > 0.3
            return is_vcp, tightness

        except Exception:
            return False, 0.0

    def _count_bases(self, close: pd.Series, ma50: pd.Series) -> int:
        """
        Count the number of bases formed during the current advance.

        A base = Period where price pulls back to or below MA50, then recovers.
        1st base breakout = Most powerful (highest success rate).
        3rd+ base = Failure-prone (late stage).
        """
        try:
            if len(close) < 50:
                return 0

            # Look at last 252 days
            lookback = min(252, len(close))
            c = close.iloc[-lookback:].values.astype(float)
            m = ma50.iloc[-lookback:].dropna().values.astype(float)

            if len(m) < 50:
                return 0

            # Align lengths
            min_len = min(len(c), len(m))
            c = c[-min_len:]
            m = m[-min_len:]

            # Count transitions: above MA50 → below MA50 → above MA50 = 1 base
            above = c > m
            bases = 0
            was_above = above[0]
            touched_below = False

            for i in range(1, len(above)):
                if was_above and not above[i]:
                    touched_below = True
                elif touched_below and above[i]:
                    bases += 1
                    touched_below = False
                was_above = above[i]

            return bases

        except Exception:
            return 0

    def _base_depth(self, close: pd.Series, lookback: int = 60) -> float:
        """
        Calculate the depth of the current correction from the recent high.

        < 15%: Very tight (bullish)
        15-25%: Normal correction
        25-35%: Deep but acceptable for growth stocks
        > 35%: Too deep (red flag)
        """
        try:
            if len(close) < 10:
                return 0.0

            period = min(lookback, len(close))
            recent = close.iloc[-period:].astype(float)
            high = float(recent.max())
            current = float(recent.iloc[-1])

            if high <= 0:
                return 0.0

            depth = (high - current) / high * 100
            return max(0.0, depth)

        except Exception:
            return 0.0
