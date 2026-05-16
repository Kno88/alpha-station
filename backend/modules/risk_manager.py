"""
Alpha Station v5.0 — Risk Management Module

Institutional-grade position sizing and risk management.
Rules:
  1. Never risk more than 1% of portfolio on a single trade
  2. Never allocate more than 10% to a single position
  3. Stop loss based on ATR (volatility-adjusted)
  4. Target minimum 3:1 reward-to-risk ratio
  5. Position size = Risk $ / Risk per Share

Key metrics:
  - ATR (Average True Range) — Volatility measurement
  - Position Size — Shares to buy for 1% risk
  - Stop Loss — ATR-based or MA-based (whichever is tighter)
  - R-Multiple — Potential reward in units of risk
  - Portfolio Heat — Total portfolio exposure to risk
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from loguru import logger

from config import settings
from models import RiskMetrics, StageResult


class RiskManager:
    """
    Computes institutional risk management metrics.

    Core principle: Size your position based on RISK, not conviction.
    A $100k portfolio with 1% risk = $1,000 max loss per trade.
    If stop is $5 from entry → Position = $1,000 / $5 = 200 shares.
    """

    def compute(
        self,
        ticker: str,
        df: pd.DataFrame,
        stage: StageResult,
        portfolio_size: float | None = None,
    ) -> RiskMetrics:
        """Compute risk metrics for a ticker."""
        try:
            portfolio = portfolio_size or settings.default_portfolio_size
            price = float(df["Close"].iloc[-1])

            # ── ATR Calculation ──────────────────────────────────────────────
            atr_14 = self._calculate_atr(df, period=14)
            atr_pct = (atr_14 / price * 100) if price > 0 else 0.0

            # ── Stop Loss ────────────────────────────────────────────────────
            stop_atr = price - (atr_14 * settings.atr_stop_multiplier)
            stop_ma50 = stage.ma50 if stage.ma50 > 0 else stop_atr
            stop_ma200 = stage.ma200 if stage.ma200 > 0 else stop_atr

            # Use the tightest sensible stop (closest to current price but below)
            stop_candidates = [s for s in [stop_atr, stop_ma50] if 0 < s < price]
            if not stop_candidates:
                stop_candidates = [price * 0.92]  # Fallback: 8% stop

            suggested_stop = max(stop_candidates)  # Tightest stop
            stop_loss_pct = ((price - suggested_stop) / price * 100) if price > 0 else 8.0

            # Cap stop distance at 8% max
            if stop_loss_pct > 8.0:
                suggested_stop = price * 0.92
                stop_loss_pct = 8.0

            # ── Risk Per Share ───────────────────────────────────────────────
            risk_per_share = price - suggested_stop

            # ── Position Sizing (1% portfolio risk) ──────────────────────────
            max_risk_dollars = portfolio * settings.max_risk_per_trade_pct
            if risk_per_share > 0:
                position_shares = int(max_risk_dollars / risk_per_share)
            else:
                position_shares = 0

            position_dollars = position_shares * price
            position_pct = (position_dollars / portfolio * 100) if portfolio > 0 else 0.0

            # Cap position at max_position_pct
            max_dollars = portfolio * settings.max_position_pct
            if position_dollars > max_dollars:
                position_shares = int(max_dollars / price)
                position_dollars = position_shares * price
                position_pct = (position_dollars / portfolio * 100)

            # ── Reward Target ────────────────────────────────────────────────
            reward_target = self._calculate_reward_target(
                price, stage, atr_14
            )
            reward_per_share = reward_target - price
            risk_reward_ratio = (reward_per_share / risk_per_share) if risk_per_share > 0 else 0.0
            r_multiple = risk_reward_ratio  # Same concept

            # ── 52-week high for resistance ──────────────────────────────────
            lookback = min(252, len(df))
            high_52w = float(df["Close"].iloc[-lookback:].max())

            # ── Portfolio heat contribution ──────────────────────────────────
            heat = (risk_per_share * position_shares / portfolio * 100) if portfolio > 0 else 0.0

            return RiskMetrics(
                ticker=ticker,
                atr_14=round(atr_14, 2),
                atr_pct=round(atr_pct, 2),
                suggested_stop_loss=round(suggested_stop, 2),
                stop_loss_pct=round(stop_loss_pct, 2),
                position_size_shares=position_shares,
                position_size_dollars=round(position_dollars, 2),
                position_pct_portfolio=round(position_pct, 2),
                risk_per_share=round(risk_per_share, 2),
                reward_target=round(reward_target, 2),
                risk_reward_ratio=round(risk_reward_ratio, 2),
                r_multiple_potential=round(r_multiple, 2),
                support_ma50=round(stage.ma50, 2),
                support_ma200=round(stage.ma200, 2),
                resistance_52w_high=round(high_52w, 2),
                max_position_pct=settings.max_position_pct * 100,
                portfolio_heat_contribution=round(heat, 2),
            )

        except Exception as e:
            logger.error(f"Risk calculation error for {ticker}: {e}")
            return self._default_result(ticker, stage)

    # ── Private helpers ──────────────────────────────────────────────────────

    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Average True Range — Measures volatility.
        TR = max(H-L, |H-Prev_C|, |L-Prev_C|)
        ATR = SMA(TR, period)
        """
        try:
            high = df["High"].astype(float)
            low = df["Low"].astype(float)
            close = df["Close"].astype(float)

            prev_close = close.shift(1)

            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)

            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = float(tr.rolling(period).mean().iloc[-1])

            return atr if not np.isnan(atr) else 0.0
        except Exception:
            return 0.0

    def _calculate_reward_target(
        self,
        price: float,
        stage: StageResult,
        atr: float,
    ) -> float:
        """
        Estimate reward target based on stage and historical extensions.

        Stage 2 (early): Target 20-30% above entry (1st base breakout)
        Stage 2 (mid):   Target 15-20% above entry
        Stage 2 (late):  Target 10-15% above entry
        Stage 1→2:       Target 25% above entry (fresh breakout)
        Stage 3/4:       Target 5-10% (defensive)
        """
        try:
            if stage.stage.value == "Stage 2":
                if stage.stage_weeks <= 8:
                    # Early Stage 2 — biggest potential
                    target_pct = 0.25
                elif stage.stage_weeks <= 20:
                    # Mid Stage 2
                    target_pct = 0.18
                else:
                    # Late Stage 2 — extended, reduced target
                    target_pct = 0.12
            elif stage.transitioning_to_2:
                target_pct = 0.25  # Fresh breakout potential
            elif stage.stage.value == "Stage 1":
                target_pct = 0.15
            else:
                target_pct = 0.08  # Defensive

            target = price * (1 + target_pct)

            # Ensure target is reasonable (at least 2x ATR above entry)
            min_target = price + (atr * 4)
            return max(target, min_target)

        except Exception:
            return price * 1.15  # Default 15%

    def _default_result(self, ticker: str, stage: StageResult) -> RiskMetrics:
        """Default risk metrics when calculation fails."""
        return RiskMetrics(
            ticker=ticker,
            atr_14=0.0,
            atr_pct=0.0,
            suggested_stop_loss=0.0,
            stop_loss_pct=8.0,
            position_size_shares=0,
            position_size_dollars=0.0,
            position_pct_portfolio=0.0,
            risk_per_share=0.0,
            reward_target=0.0,
            risk_reward_ratio=0.0,
            r_multiple_potential=0.0,
            support_ma50=stage.ma50,
            support_ma200=stage.ma200,
            resistance_52w_high=0.0,
        )
