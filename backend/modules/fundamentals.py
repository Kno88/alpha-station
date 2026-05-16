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


# ── FASE 2: Calculation Helpers ────────────────────────────────────────────────

def estimate_moat(info: dict) -> str:
    """Heuristic estimate of Economic Moat based on margins."""
    net_margin = info.get("profitMargins", 0)
    gross_margin = info.get("grossMargins", 0)
    
    if net_margin is not None and gross_margin is not None:
        if net_margin > 0.20 and gross_margin > 0.50:
            return "Wide"
        elif net_margin > 0.10 and gross_margin > 0.30:
            return "Narrow"
    return "None"

def estimate_market_share(info: dict) -> float:
    """Heuristic estimate of Market Share based on Revenue."""
    rev = info.get("totalRevenue", 0)
    if rev is None or rev == 0:
        return 0.0
    
    if rev > 100e9:
        return 35.0
    elif rev > 10e9:
        return 15.0
    elif rev > 1e9:
        return 5.0
    return 1.0


# ── TIER-1 GROWTH QUALITY CALCULATORS ─────────────────────────────────────────

def calculate_rule_of_40(revenue_growth_yoy: Optional[float], fcf_margin: Optional[float]) -> Optional[float]:
    """
    Rule of 40: Revenue Growth% + FCF Margin% >= 40 = elite SaaS/growth company.
    Used by institutional investors to filter high-quality growth companies.
    """
    if revenue_growth_yoy is None or fcf_margin is None:
        return None
    return round((revenue_growth_yoy * 100) + (fcf_margin * 100), 1)


def calculate_operating_leverage(stock: yf.Ticker) -> Optional[float]:
    """
    Operating Leverage = Operating Income Growth / Revenue Growth.
    Ratio > 1 means operating income is growing faster than revenue (expanding margins).
    This is a key signal for hidden growth potential.
    """
    try:
        yearly = stock.yearly_financials
        if yearly is None or yearly.empty:
            return None

        if "Total Revenue" not in yearly.index or "Operating Income" not in yearly.index:
            return None

        rev = yearly.loc["Total Revenue"].dropna().sort_index(ascending=False)
        op = yearly.loc["Operating Income"].dropna().sort_index(ascending=False)

        if len(rev) < 2 or len(op) < 2:
            return None

        rev_current, rev_prior = float(rev.iloc[0]), float(rev.iloc[1])
        op_current, op_prior = float(op.iloc[0]), float(op.iloc[1])

        if rev_prior == 0 or op_prior == 0:
            return None

        rev_growth = (rev_current - rev_prior) / abs(rev_prior)
        op_growth = (op_current - op_prior) / abs(op_prior)

        if rev_growth == 0:
            return None

        leverage = op_growth / rev_growth
        return round(max(-5.0, min(10.0, leverage)), 2)  # clamp
    except Exception:
        return None


def calculate_gross_margin_expansion(stock: yf.Ticker) -> Optional[float]:
    """
    Gross Margin Expansion = GM_current - GM_prior_year.
    Positive = improving unit economics (pricing power or cost discipline).
    """
    try:
        yearly = stock.yearly_financials
        if yearly is None or yearly.empty:
            return None

        if "Gross Profit" not in yearly.index or "Total Revenue" not in yearly.index:
            return None

        gp = yearly.loc["Gross Profit"].dropna().sort_index(ascending=False)
        rev = yearly.loc["Total Revenue"].dropna().sort_index(ascending=False)

        if len(gp) < 2 or len(rev) < 2:
            return None

        gm_current = float(gp.iloc[0]) / float(rev.iloc[0]) if float(rev.iloc[0]) != 0 else None
        gm_prior = float(gp.iloc[1]) / float(rev.iloc[1]) if float(rev.iloc[1]) != 0 else None

        if gm_current is None or gm_prior is None:
            return None

        return round(gm_current - gm_prior, 4)  # e.g. 0.03 = +3pp expansion
    except Exception:
        return None


def calculate_rd_to_revenue(info: dict) -> Optional[float]:
    """
    R&D Spend / Revenue. High R&D intensity (>10%) in tech/pharma signals
    future moat building — often undervalued by market (Lev & Sougiannis effect).
    """
    try:
        rd = info.get("researchDevelopment")
        revenue = info.get("totalRevenue")
        if rd is None or revenue is None or revenue == 0:
            return None
        return round(abs(rd) / revenue, 4)
    except Exception:
        return None


def calculate_revenue_per_employee(info: dict) -> Optional[float]:
    """
    Revenue / Full-Time Employees. Asset-light efficiency metric.
    >$500K per employee = highly scalable business model.
    """
    try:
        revenue = info.get("totalRevenue")
        employees = info.get("fullTimeEmployees")
        if revenue is None or employees is None or employees == 0:
            return None
        return round(revenue / employees, 0)
    except Exception:
        return None


def calculate_altman_z_score(info: dict) -> Optional[float]:
    """
    Altman Z-Score (bankruptcy predictor).
    Formula: 1.2*X1 + 1.4*X2 + 3.3*X3 + 0.6*X4 + 1.0*X5
    X1 = Working Capital / Total Assets
    X2 = Retained Earnings / Total Assets
    X3 = EBIT / Total Assets
    X4 = Market Cap / Total Liabilities
    X5 = Sales / Total Assets
    """
    try:
        current_assets = info.get("currentAssets")
        current_liabilities = info.get("currentLiabilities")
        total_assets = info.get("totalAssets")
        retained_earnings = info.get("retainedEarnings")
        ebit = info.get("operatingIncome")  # close proxy for EBIT
        market_cap = info.get("marketCap")
        total_liabilities = info.get("totalLiabilities")
        sales = info.get("totalRevenue")

        if not all([current_assets, current_liabilities, total_assets, 
                    retained_earnings, ebit, market_cap, total_liabilities, sales]):
            return None
        
        if total_assets == 0 or total_liabilities == 0:
            return None

        working_capital = current_assets - current_liabilities
        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit / total_assets
        x4 = market_cap / total_liabilities
        x5 = sales / total_assets

        z_score = (1.2 * x1) + (1.4 * x2) + (3.3 * x3) + (0.6 * x4) + (1.0 * x5)
        return float(z_score)
    except Exception:
        return None

def calculate_revenue_cagr_3y(stock: yf.Ticker) -> Optional[float]:
    """
    Calculate 3-Year Revenue CAGR (Compound Annual Growth Rate)
    Formula: (Revenue_Current / Revenue_3Y_Ago)^(1/3) - 1
    """
    try:
        yearly = stock.yearly_financials
        if yearly is None or yearly.empty or "Total Revenue" not in yearly.index:
            return None

        rev_data = yearly.loc["Total Revenue"].dropna().sort_index(ascending=False)
        if len(rev_data) < 2:
            return None

        # Get current year and year 3 years ago
        current_rev = float(rev_data.iloc[0])
        rev_3y_ago = float(rev_data.iloc[min(3, len(rev_data) - 1)])

        if current_rev <= 0 or rev_3y_ago <= 0:
            return None

        # CAGR = (Ending / Beginning)^(1/n) - 1
        cagr = (current_rev / rev_3y_ago) ** (1 / 3) - 1
        return max(-1.0, cagr)  # Cap at -100%

    except Exception:
        return None


def calculate_fcf_quality(info: dict) -> Optional[float]:
    """
    Calculate FCF to Net Income ratio (Earnings Quality)
    High ratio (>0.8) = earnings are backed by real cash
    Low ratio (<0.5) = accounting profits, not cash (red flag)
    """
    try:
        fcf = info.get("freeCashflow")
        net_income = info.get("netIncome")

        if fcf is None or net_income is None or net_income == 0:
            return None

        ratio = fcf / net_income
        return max(0.0, min(2.0, ratio))  # Clamp between 0 and 2

    except Exception:
        return None


def calculate_roic(info: dict) -> Optional[float]:
    """
    ROIC = NOPAT / Invested Capital
    NOPAT = EBIT * (1 - Tax Rate)
    Invested Capital = Total Assets - Current Liabilities
    """
    try:
        ebit = info.get("operatingIncome")
        net_income = info.get("netIncome")
        total_assets = info.get("totalAssets")
        current_liabilities = info.get("currentLiabilities")

        if not all([ebit, net_income, total_assets, current_liabilities]):
            return None

        # Estimate tax rate from net income and EBIT
        if ebit == 0:
            return None
        tax_rate = max(0, 1 - (net_income / ebit))
        tax_rate = min(0.5, tax_rate)  # Cap at 50%

        nopat = ebit * (1 - tax_rate)
        invested_capital = total_assets - current_liabilities

        if invested_capital <= 0:
            return None

        roic = nopat / invested_capital
        return max(-1.0, min(2.0, roic))  # Clamp -100% to 200%

    except Exception:
        return None


def calculate_fcf_growth(info: dict, stock: yf.Ticker) -> Optional[float]:
    """
    FCF Growth = (FCF_Current / FCF_Prior_Year) - 1
    Extracts from cash flow statement: Operating Cash Flow - CapEx
    """
    try:
        # Primary: use provided freeCashflow if recent data is available
        fcf_current = info.get("freeCashflow")

        # Try to extract from cash flow statement for better precision
        try:
            cash_flow = stock.cashflow
            if cash_flow is not None and not cash_flow.empty and len(cash_flow.columns) >= 2:
                # Look for Operating Cash Flow and CapEx
                ocf_values = []
                capex_values = []

                if "Operating Cash Flow" in cash_flow.index:
                    ocf_values = cash_flow.loc["Operating Cash Flow"].dropna().values

                if "Capital Expenditure" in cash_flow.index:
                    capex_values = cash_flow.loc["Capital Expenditure"].dropna().values

                if len(ocf_values) >= 2 and len(capex_values) >= 2:
                    # Calculate FCF for current and prior year
                    fcf_curr = float(ocf_values[0]) - abs(float(capex_values[0]))
                    fcf_prior = float(ocf_values[1]) - abs(float(capex_values[1]))

                    if fcf_prior != 0 and fcf_curr is not None:
                        growth = (fcf_curr / fcf_prior) - 1
                        return max(-1.0, min(5.0, growth))  # Clamp -100% to 400%
        except Exception:
            pass

        # Fallback to info freeCashflow if available
        if fcf_current is not None and fcf_current > 0:
            # Can't calculate growth without prior year, return None
            return None

        return None

    except Exception:
        return None


def calculate_fcf_margin(info: dict) -> Optional[float]:
    """
    FCF Margin = Free Cash Flow / Revenue
    Shows how much of revenue converts to free cash
    >10% = excellent, 5-10% = good, <5% = weak
    """
    try:
        fcf = info.get("freeCashflow")
        revenue = info.get("totalRevenue")

        if fcf is None or revenue is None or revenue == 0:
            return None

        margin = fcf / revenue
        return max(-1.0, min(1.0, margin))  # Clamp -100% to 100%

    except Exception:
        return None


def calculate_avg_volume_20d(stock: yf.Ticker) -> Optional[float]:
    """
    Calculate average trading volume over the last 20 days
    """
    try:
        hist = stock.history(period="1mo")
        if hist is not None and not hist.empty and len(hist) >= 20:
            volumes = hist["Volume"].tail(20)
            avg_vol = volumes.mean()
            return float(avg_vol) if avg_vol > 0 else None
        return None
    except Exception:
        return None


def calculate_piotroski_f_score(stock: yf.Ticker, info: dict) -> Optional[float]:
    """
    Piotroski F-Score: 9-point quality assessment (0-9, higher is better)
    >6 = high quality, 3-6 = moderate, <3 = poor quality/fraud risk

    Metrics:
    1. Net Income > 0 (profitability)
    2. Operating Cash Flow > 0 (quality)
    3. Operating Cash Flow > Net Income (earnings quality)
    4. Change in ROA > 0 (improving profitability)
    5. Debt/Total Assets decreased (improving leverage)
    6. Current Ratio increased (improving liquidity)
    7. Shares Outstanding not diluted
    8. Gross Margin increased (operational efficiency)
    9. Asset Turnover increased (operational efficiency)
    """
    try:
        score = 0.0

        # 1. Net Income > 0
        net_income = info.get("netIncome")
        if net_income is not None and net_income > 0:
            score += 1

        # 2. Operating Cash Flow > 0
        ocf = info.get("operatingCashflow")
        if ocf is not None and ocf > 0:
            score += 1

        # 3. OCF > Net Income (earnings quality)
        if ocf is not None and net_income is not None and ocf > net_income:
            score += 1

        # 4. Change in ROA > 0 (improving)
        try:
            yearly = stock.yearly_financials
            if yearly is not None and not yearly.empty:
                # Compare current year to prior year ROA
                total_assets = info.get("totalAssets")
                net_income_current = info.get("netIncome")

                if total_assets is not None and net_income_current is not None and total_assets > 0:
                    roa_current = net_income_current / total_assets
                    # Try to get prior year
                    if len(yearly.columns) >= 2:
                        # Simplified: just check if current ROA is positive
                        if roa_current > 0:
                            score += 1
        except Exception:
            pass

        # 5. Debt/Total Assets decreased (or low)
        try:
            total_debt = info.get("totalDebt")
            total_assets = info.get("totalAssets")
            if total_debt is not None and total_assets is not None and total_assets > 0:
                debt_ratio = total_debt / total_assets
                if debt_ratio < 0.5:  # Less than 50% debt
                    score += 1
        except Exception:
            pass

        # 6. Current Ratio > 1.5 (good liquidity)
        current_ratio = info.get("currentRatio")
        if current_ratio is not None and current_ratio > 1.5:
            score += 1

        # 7. Shares Outstanding check (not diluted - simplified)
        # Skip for now, would need historical comparison

        # 8. Gross Margin > 30% (operational efficiency)
        gross_margin = info.get("grossMargins")
        if gross_margin is not None and gross_margin > 0.30:
            score += 1

        # 9. Asset Turnover increasing (simplified: Revenue/Assets > 1)
        try:
            revenue_ttm = info.get("totalRevenue")
            total_assets = info.get("totalAssets")
            if revenue_ttm is not None and total_assets is not None and total_assets > 0:
                asset_turnover = revenue_ttm / total_assets
                if asset_turnover > 0.5:  # Reasonable efficiency
                    score += 1
        except Exception:
            pass

        return score  # 0-9

    except Exception:
        return None


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
                altman_z_score=None,
                earnings_surprise_pct=None,
                accruals_ratio=None,
                fcf_to_net_income=None,
                insider_ownership_pct=None,
                # New Moat & Checklist fields
                moat="None",
                market_share_pct=0.0,
                rule_of_40=None,
                operating_leverage=None,
                gross_margin_expansion=None,
                net_cash_position=None,
                is_net_cash=False,
                rd_to_revenue=None,
                insider_net_buying=None,
                low_analyst_coverage=False,
                revenue_per_employee=None,
                revenue_accelerating=False,
                earnings_positive=False,
                low_institutional_coverage=False,
                high_growth=False,
                profitable=False,
                positive_fcf=False,
                low_debt=False
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
        _trailing_pe = info.get("trailingPE")
        pe_ratio = _trailing_pe if _trailing_pe is not None else info.get("forwardPE")
        ps_ratio = info.get("priceToSalesTrailing12Months")
        price_to_book = info.get("priceToBook")
        forward_pe = info.get("forwardPE")
        ev_to_ebitda = info.get("enterpriseToEbitda")

        # Calculate PEG Ratio (P/E / Earnings Growth Rate)
        peg_ratio = None
        if pe_ratio is not None and earnings_growth_yoy is not None and earnings_growth_yoy > 0:
            peg_ratio = pe_ratio / (earnings_growth_yoy * 100)

        # ── Balance Sheet & Income Statement Variables ───────────────────────
        total_debt = info.get("totalDebt")
        total_equity = info.get("totalStockholderEquity") or info.get("totalEquity")
        total_assets = info.get("totalAssets")
        total_liabilities = info.get("totalLiabilities")
        cash_and_equiv = info.get("cashAndCashEquivalents") or info.get("cash")
        ebitda = info.get("ebitda")
        net_income = info.get("netIncome") or info.get("netIncomeToCommon")
        operating_income_val = info.get("operatingIncome")
        current_assets = info.get("currentAssets")
        current_liabilities = info.get("currentLiabilities")

        # Fallback for Balance Sheet & Income Statement items (yfinance info is often null for these)
        try:
            # 1. Try Balance Sheet for Equity, Debt, Assets, Liabilities
            if any(v is None for v in [total_equity, total_assets, total_debt, total_liabilities]):
                bs = stock.balance_sheet
                if bs is not None and not bs.empty:
                    # Equity fallbacks
                    for k in ["Stockholders Equity", "Total Equity Gross Minority Interest", "Common Stock Equity", "StockholdersEquity"]:
                        if k in bs.index:
                            total_equity = float(bs.loc[k].iloc[0])
                            break
                    
                    # Assets & Liabilities fallbacks
                    if "Total Assets" in bs.index: total_assets = float(bs.loc["Total Assets"].iloc[0])
                    if "Total Liabilities Net Minority Interest" in bs.index: 
                        total_liabilities = float(bs.loc["Total Liabilities Net Minority Interest"].iloc[0])
                    elif "Total Liabilities" in bs.index:
                        total_liabilities = float(bs.loc["Total Liabilities"].iloc[0])
                    
                    # Debt fallbacks
                    if "Total Debt" in bs.index: total_debt = float(bs.loc["Total Debt"].iloc[0])
                    
                    # Current Ratio components
                    if "Current Assets" in bs.index: current_assets = float(bs.loc["Current Assets"].iloc[0])
                    if "Current Liabilities" in bs.index: current_liabilities = float(bs.loc["Current Liabilities"].iloc[0])
            
            # 2. Try Income Statement for Net Income, EBITDA, Operating Income
            if any(v is None for v in [net_income, ebitda, operating_income_val]):
                is_stmt = stock.income_stmt
                if is_stmt is not None and not is_stmt.empty:
                    # Net Income fallbacks
                    for k in ["Net Income", "Net Income Common Stockholders", "NetIncome"]:
                        if k in is_stmt.index:
                            net_income = float(is_stmt.loc[k].iloc[0])
                            break
                    
                    if "EBITDA" in is_stmt.index: ebitda = float(is_stmt.loc["EBITDA"].iloc[0])
                    if "Operating Income" in is_stmt.index: operating_income_val = float(is_stmt.loc["Operating Income"].iloc[0])

        except Exception as e:
            logger.warning(f"Fallback data extraction failed for {ticker}: {e}")

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
        operating_margin = None
        if operating_income_val is not None and revenue_ttm is not None and revenue_ttm != 0:
            operating_margin = operating_income_val / revenue_ttm

        # ── V5.0 Institutional Metrics ───────────────────────────────────────
        fcf = info.get("freeCashflow")
        
        fcf_yield = None
        if fcf is not None and market_cap is not None and market_cap > 0:
            fcf_yield = fcf / market_cap

        earnings_yield = None
        if pe_ratio is not None and pe_ratio > 0:
            earnings_yield = 1.0 / pe_ratio

        debt_to_fcf = None
        if total_debt is not None and fcf is not None and fcf > 0:
            debt_to_fcf = total_debt / fcf

        capex_to_revenue = None
        # Approximate capex from FCF formula if unavailable directly: CapEx = OCF - FCF
        ocf = info.get("operatingCashflow")
        if ocf is not None and fcf is not None and revenue_ttm is not None and revenue_ttm > 0:
            capex = ocf - fcf
            capex_to_revenue = capex / revenue_ttm

        # ROE = Net Income / Shareholder Equity
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
        positive_fcf = fcf is not None and fcf > 0
        low_debt = debt_to_equity is not None and debt_to_equity < 1.5

        # ── TIER-1 GROWTH QUALITY SIGNALS ────────────────────────────────────────
        fcf_margin_val = calculate_fcf_margin(info)
        rule_of_40 = calculate_rule_of_40(revenue_growth_yoy, fcf_margin_val)
        operating_leverage_val = calculate_operating_leverage(stock)
        gross_margin_expansion_val = calculate_gross_margin_expansion(stock)

        # Net Cash Position
        net_cash_position = None
        is_net_cash = False
        if cash_and_equiv is not None and total_debt is not None:
            net_cash_position = cash_and_equiv - total_debt
            is_net_cash = net_cash_position > 0

        # R&D Intensity
        rd_to_revenue_val = calculate_rd_to_revenue(info)

        # Insider Net Buying (heuristic: high insider ownership + >1% = aligned)
        insider_net_buying = None
        if insider_pct is not None:
            insider_net_buying = insider_pct > 1.0  # simplified proxy

        # Low Analyst Coverage (< 5 analysts = potential undiscovered gem)
        n_analysts = info.get("numberOfAnalystOpinions")
        low_analyst_coverage = n_analysts is not None and n_analysts < 5

        # Revenue per Employee
        revenue_per_employee_val = calculate_revenue_per_employee(info)

        # Price history (last 20 trading days closing prices) — reuses history call
        price_history_20d = None
        try:
            hist = stock.history(period="1mo")
            if hist is not None and not hist.empty and len(hist) >= 2:
                closes = hist["Close"].tail(20).tolist()
                price_history_20d = [round(float(p), 2) for p in closes]
        except Exception:
            pass

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
            fcf_yield=fcf_yield,
            earnings_yield=earnings_yield,
            # Crecimiento
            revenue_ttm=revenue_ttm,
            revenue_growth_yoy=revenue_growth_yoy,
            revenue_growth_qoq=revenue_growth_qoq,
            revenue_cagr_3y=calculate_revenue_cagr_3y(stock),
            earnings_growth_yoy=earnings_growth_yoy,
            earnings_growth_qoq=None,  # TODO: extract from quarterly financials
            fcf_growth=calculate_fcf_growth(info, stock),
            capex_to_revenue=capex_to_revenue,
            # Rentabilidad
            gross_margin=gross_margin,
            operating_margin=operating_margin,
            net_margin=net_margin,
            fcf_margin=calculate_fcf_margin(info),
            roe=roe,
            roa=roa,
            roic=calculate_roic(info),
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
            debt_to_fcf=debt_to_fcf,
            # Liquidez
            avg_volume_20d=calculate_avg_volume_20d(stock),
            current_volume=info.get("volume"),
            float_shares=float_shares,
            short_float_pct=short_pct,
            # Institucional
            institutional_ownership_pct=inst_pct,
            insider_ownership_pct=insider_pct,
            # Calidad
            piotroski_f_score=calculate_piotroski_f_score(stock, info),
            altman_z_score=calculate_altman_z_score(info),
            earnings_surprise_pct=None,  # TODO: from earnings history
            accruals_ratio=None,  # TODO: calculate
            fcf_to_net_income=calculate_fcf_quality(info),
            # Checklist booleans
            revenue_accelerating=revenue_accelerating,
            earnings_positive=earnings_positive,
            low_institutional_coverage=low_inst_coverage,
            high_growth=high_growth,
            profitable=profitable,
            positive_fcf=positive_fcf,
            low_debt=low_debt,
            moat=estimate_moat(info),
            market_share_pct=estimate_market_share(info),
            # Tier-1 Growth Quality Signals
            rule_of_40=rule_of_40,
            operating_leverage=operating_leverage_val,
            gross_margin_expansion=gross_margin_expansion_val,
            net_cash_position=net_cash_position,
            is_net_cash=is_net_cash,
            rd_to_revenue=rd_to_revenue_val,
            insider_net_buying=insider_net_buying,
            low_analyst_coverage=low_analyst_coverage,
            revenue_per_employee=revenue_per_employee_val,
            price_history_20d=price_history_20d,
        )
