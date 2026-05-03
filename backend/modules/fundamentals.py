"""
Alpha Station v4.0 — Fundamentals Engine

Pulls fundamental data via yfinance (free, no API key required).
Optional: Financial Modeling Prep (FMP) for richer data with API key.
"""

from __future__ import annotations

from typing import Optional

import yfinance as yf
from loguru import logger

from models import FundamentalResult


class FundamentalsEngine:
    """Fetches and scores fundamental data for growth stock screening."""

    # Hidden Gem thresholds
    LOW_INST_OWNERSHIP_PCT = 40.0      # Below this = under-covered
    HIGH_REVENUE_GROWTH_PCT = 0.20     # 20% YoY minimum for "high growth"
    SMALL_MID_CAP_MAX = 10_000_000_000  # $10B market cap ceiling

    async def fetch(self, ticker: str) -> FundamentalResult:
        try:
            return await self._fetch_yfinance(ticker)
        except Exception as e:
            logger.error(f"Fundamentals error for {ticker}: {e}")
            return FundamentalResult(
                ticker=ticker,
                company_name=ticker,
                sector=None,
                industry=None,
                market_cap=None,
                revenue_growth_yoy=None,
                revenue_growth_qoq=None,
                earnings_growth_yoy=None,
                gross_margin=None,
                net_margin=None,
                revenue_ttm=None,
                pe_ratio=None,
                ps_ratio=None,
                institutional_ownership_pct=None,
                short_float_pct=None,
                float_shares=None,
            )

    async def _fetch_yfinance(self, ticker: str) -> FundamentalResult:
        stock = yf.Ticker(ticker)
        try:
            info = stock.info or {}
        except Exception:
            info = {}

        # ── Core metrics ─────────────────────────────────────────────────────
        company_name = info.get("longName") or info.get("shortName") or ticker
        sector = info.get("sector")
        industry = info.get("industry")
        market_cap = info.get("marketCap")

        # ── Revenue growth ────────────────────────────────────────────────────
        revenue_growth_yoy = info.get("revenueGrowth")  # yfinance gives this as float (0.25 = 25%)
        earnings_growth_yoy = info.get("earningsGrowth")

        # QoQ from quarterly financials
        revenue_growth_qoq = None
        try:
            quarterly = stock.quarterly_financials
            if quarterly is not None and not quarterly.empty and "Total Revenue" in quarterly.index:
                rev_rows = quarterly.loc["Total Revenue"].dropna()
                if len(rev_rows) >= 2:
                    q_latest = float(rev_rows.iloc[0])
                    q_prior = float(rev_rows.iloc[1])
                    if q_prior != 0:
                        revenue_growth_qoq = (q_latest - q_prior) / abs(q_prior)
        except Exception:
            pass

        # ── Margins ──────────────────────────────────────────────────────────
        gross_margin = info.get("grossMargins")
        net_margin = info.get("profitMargins")

        # ── Revenue TTM ──────────────────────────────────────────────────────
        revenue_ttm = info.get("totalRevenue")

        # ── Valuation ────────────────────────────────────────────────────────
        pe_ratio = info.get("trailingPE") or info.get("forwardPE")
        ps_ratio = info.get("priceToSalesTrailing12Months")

        # ── Ownership ────────────────────────────────────────────────────────
        inst_ownership = info.get("heldPercentInstitutions")
        inst_pct = inst_ownership * 100 if inst_ownership is not None else None

        short_float = info.get("shortPercentOfFloat")
        short_pct = short_float * 100 if short_float is not None else None

        float_shares = info.get("floatShares")

        # ── Checklist booleans ────────────────────────────────────────────────
        high_growth = (
            revenue_growth_yoy is not None
            and revenue_growth_yoy >= self.HIGH_REVENUE_GROWTH_PCT
        )

        revenue_accelerating = (
            revenue_growth_qoq is not None
            and revenue_growth_yoy is not None
            and revenue_growth_qoq > revenue_growth_yoy
        )

        earnings_positive = (
            net_margin is not None and net_margin > 0
        ) or (
            earnings_growth_yoy is not None and earnings_growth_yoy > 0
        )

        low_inst_coverage = (
            inst_pct is not None and inst_pct < self.LOW_INST_OWNERSHIP_PCT
        )

        return FundamentalResult(
            ticker=ticker,
            company_name=company_name,
            sector=sector,
            industry=industry,
            market_cap=market_cap,
            revenue_growth_yoy=revenue_growth_yoy,
            revenue_growth_qoq=revenue_growth_qoq,
            earnings_growth_yoy=earnings_growth_yoy,
            gross_margin=gross_margin,
            net_margin=net_margin,
            revenue_ttm=revenue_ttm,
            pe_ratio=pe_ratio,
            ps_ratio=ps_ratio,
            institutional_ownership_pct=inst_pct,
            short_float_pct=short_pct,
            float_shares=float_shares,
            revenue_accelerating=revenue_accelerating,
            earnings_positive=earnings_positive,
            low_institutional_coverage=low_inst_coverage,
            high_growth=high_growth,
        )
