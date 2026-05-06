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
                # Default None for all new fields
                peg_ratio=None,
                ev_to_ebitda=None,
                price_to_book=None,
                forward_pe=None,
                revenue_cagr_3y=None,
                fcf_growth=None,
                operating_margin=None,
                fcf_margin=None,
                roe=None,
                roa=None,
                roic=None,
                total_debt=None,
                total_equity=None,
                total_assets=None,
                cash_and_equiv=None,
                debt_to_equity=None,
                debt_to_ebitda=None,
                current_ratio=None,
                quick_ratio=None,
                interest_coverage=None,
                net_debt=None,
                piotroski_f_score=None,
                earnings_surprise_pct=None,
                accruals_ratio=None,
                fcf_to_net_income=None,
                insider_ownership_pct=None,
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
        price_to_book = info.get("priceToBook")
        forward_pe = info.get("forwardPE")
        ev_to_ebitda = info.get("enterpriseToEbitda")

        # Calculate PEG Ratio (P/E / Earnings Growth Rate)
        peg_ratio = None
        if pe_ratio is not None and earnings_growth_yoy is not None and earnings_growth_yoy > 0:
            peg_ratio = pe_ratio / (earnings_growth_yoy * 100)

        # ── Balance Sheet ────────────────────────────────────────────────────
        total_debt = info.get("totalDebt")
        total_equity = info.get("totalStockholderEquity")
        total_assets = info.get("totalAssets")
        cash_and_equiv = info.get("cashAndCashEquivalents")
        ebitda = info.get("ebitda")

        # Calculate derived metrics
        debt_to_equity = None
        if total_debt is not None and total_equity is not None and total_equity != 0:
            debt_to_equity = total_debt / total_equity

        debt_to_ebitda = None
        if total_debt is not None and ebitda is not None and ebitda != 0:
            debt_to_ebitda = total_debt / ebitda

        net_debt = None
        if total_debt is not None and cash_and_equiv is not None:
            net_debt = total_debt - cash_and_equiv

        # Current & Quick Ratios
        current_assets = info.get("currentAssets")
        current_liabilities = info.get("currentLiabilities")
        inventory = info.get("inventory")

        current_ratio = None
        if current_assets is not None and current_liabilities is not None and current_liabilities != 0:
            current_ratio = current_assets / current_liabilities

        quick_ratio = None
        if current_assets is not None and inventory is not None and current_liabilities is not None and current_liabilities != 0:
            quick_ratio = (current_assets - inventory) / current_liabilities

        # Interest Coverage (EBIT / Interest Expense)
        interest_coverage = None
        operating_income = info.get("operatingIncome")
        interest_expense = info.get("interestExpense")
        if operating_income is not None and interest_expense is not None and interest_expense != 0:
            interest_coverage = operating_income / interest_expense

        # ── Profitability Ratios ────────────────────────────────────────────
        operating_income_val = info.get("operatingIncome")
        operating_margin = None
        if operating_income_val is not None and revenue_ttm is not None and revenue_ttm != 0:
            operating_margin = operating_income_val / revenue_ttm

        # ROE = Net Income / Shareholder Equity
        net_income = info.get("netIncome")
        roe = None
        if net_income is not None and total_equity is not None and total_equity != 0:
            roe = net_income / total_equity

        # ROA = Net Income / Total Assets
        roa = None
        if net_income is not None and total_assets is not None and total_assets != 0:
            roa = net_income / total_assets

        # ── Ownership ────────────────────────────────────────────────────────
        inst_ownership = info.get("heldPercentInstitutions")
        inst_pct = inst_ownership * 100 if inst_ownership is not None else None

        insider_ownership = info.get("heldPercentInsiders")
        insider_pct = insider_ownership * 100 if insider_ownership is not None else None

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

        # Additional checklist booleans
        profitable = net_margin is not None and net_margin > 0
        positive_fcf = False  # TODO: calculate from cash flow statement
        low_debt = debt_to_equity is not None and debt_to_equity < 1.5

        return FundamentalResult(
            ticker=ticker,
            company_name=company_name,
            sector=sector,
            industry=industry,
            # Valuación
            market_cap=market_cap,
            pe_ratio=pe_ratio,
            ps_ratio=ps_ratio,
            peg_ratio=peg_ratio,
            ev_to_ebitda=ev_to_ebitda,
            price_to_book=price_to_book,
            forward_pe=forward_pe,
            # Crecimiento
            revenue_ttm=revenue_ttm,
            revenue_growth_yoy=revenue_growth_yoy,
            revenue_growth_qoq=revenue_growth_qoq,
            revenue_cagr_3y=None,  # TODO: calculate from historical data
            earnings_growth_yoy=earnings_growth_yoy,
            earnings_growth_qoq=None,  # TODO: extract from quarterly
            fcf_growth=None,  # TODO: calculate from cash flow
            # Rentabilidad
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            net_margin=net_margin,
            fcf_margin=None,  # TODO: calculate
            roe=roe,
            roa=roa,
            roic=None,  # TODO: calculate
            # Balance Sheet
            total_debt=total_debt,
            total_equity=total_equity,
            total_assets=total_assets,
            cash_and_equiv=cash_and_equiv,
            debt_to_equity=debt_to_equity,
            debt_to_ebitda=debt_to_ebitda,
            current_ratio=current_ratio,
            quick_ratio=quick_ratio,
            interest_coverage=interest_coverage,
            net_debt=net_debt,
            # Liquidez
            avg_volume_20d=None,  # TODO: from historical data
            current_volume=None,
            float_shares=float_shares,
            short_float_pct=short_pct,
            # Institucional
            institutional_ownership_pct=inst_pct,
            insider_ownership_pct=insider_pct,
            # Calidad
            piotroski_f_score=None,  # TODO: calculate
            earnings_surprise_pct=None,  # TODO: from earnings history
            accruals_ratio=None,  # TODO: calculate
            fcf_to_net_income=None,  # TODO: calculate
            # Checklist booleans
            revenue_accelerating=revenue_accelerating,
            earnings_positive=earnings_positive,
            low_institutional_coverage=low_inst_coverage,
            high_growth=high_growth,
            profitable=profitable,
            positive_fcf=positive_fcf,
            low_debt=low_debt,
        )
