"""
Alpha Station v5.0 — Pydantic data models

Institutional-grade models for RS Line, Risk Management, VCP detection,
and enhanced Alpha Score.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class FundamentalResult(BaseModel):
    ticker: str
    company_name: str
    sector: Optional[str]
    industry: Optional[str]

    # ── VALUACIÓN ──────────────────────────────────────────────────────────────
    market_cap: Optional[float]           # Market cap en USD
    pe_ratio: Optional[float]             # Price to Earnings
    ps_ratio: Optional[float]             # Price to Sales
    peg_ratio: Optional[float]            # P/E / Growth rate (mejor que P/E)
    ev_to_ebitda: Optional[float]         # Enterprise Value / EBITDA
    price_to_book: Optional[float]        # Price to Book Value
    forward_pe: Optional[float]           # Forward P/E (next 12 months)
    fcf_yield: Optional[float]            # Free Cash Flow Yield (FCF / Market Cap)
    earnings_yield: Optional[float]       # Earnings Yield (1 / P/E)

    # ── CRECIMIENTO ────────────────────────────────────────────────────────────
    revenue_ttm: Optional[float]          # Trailing Twelve Months Revenue
    revenue_growth_yoy: Optional[float]   # YoY % (last year vs year before)
    revenue_growth_qoq: Optional[float]   # QoQ %
    revenue_cagr_3y: Optional[float]      # 3-Year CAGR
    earnings_growth_yoy: Optional[float]  # EPS growth YoY
    earnings_growth_qoq: Optional[float]  # EPS growth QoQ
    fcf_growth: Optional[float]           # Free Cash Flow growth
    capex_to_revenue: Optional[float]     # Capex / Revenue (intensidad de capital)

    # ── RENTABILIDAD ───────────────────────────────────────────────────────────
    gross_margin: Optional[float]         # Gross Profit Margin %
    operating_margin: Optional[float]     # Operating Margin %
    net_margin: Optional[float]           # Net Profit Margin %
    fcf_margin: Optional[float]           # Free Cash Flow Margin %
    roe: Optional[float]                  # Return on Equity %
    roa: Optional[float]                  # Return on Assets %
    roic: Optional[float]                 # Return on Invested Capital %

    # ── BALANCE SHEET SALUD ────────────────────────────────────────────────────
    total_debt: Optional[float]           # Total Debt USD
    total_equity: Optional[float]         # Total Equity USD
    total_assets: Optional[float]         # Total Assets USD
    cash_and_equiv: Optional[float]       # Cash & Equivalents USD
    debt_to_equity: Optional[float]       # Debt / Equity ratio
    debt_to_ebitda: Optional[float]       # Debt / EBITDA
    current_ratio: Optional[float]        # Current Assets / Current Liabilities
    quick_ratio: Optional[float]          # (Current Assets - Inventory) / Current Liabilities
    interest_coverage: Optional[float]    # EBIT / Interest Expense
    net_debt: Optional[float]             # Total Debt - Cash
    debt_to_fcf: Optional[float]          # Total Debt / Free Cash Flow (capacidad de pago)

    # ── INSTITUCIONAL ──────────────────────────────────────────────────────────
    institutional_ownership_pct: Optional[float]  # % institucional
    insider_ownership_pct: Optional[float]        # % insiders

    # ── CALIDAD & CONSISTENCIA ─────────────────────────────────────────────────
    piotroski_f_score: Optional[float]    # 0-9, >6 = calidad
    altman_z_score: Optional[float]       # <1.8 distress, >3.0 safe
    earnings_surprise_pct: Optional[float] # % por encima/debajo de estimaciones
    accruals_ratio: Optional[float]       # Earnings quality (bajo es bueno)
    fcf_to_net_income: Optional[float]    # FCF / Net Income (calidad)
    
    # ── NUEVOS CAMPOS FUNDAMENTALES (MOAT) ─────────────────────────────────────
    moat: Optional[str] = "None"          # "Wide", "Narrow", "None"
    market_share_pct: Optional[float] = 0.0 # Cuota de mercado aproximada

    # ── TIER-1 GROWTH QUALITY SIGNALS ──────────────────────────────────────────
    rule_of_40: Optional[float] = None    # Rev Growth% + FCF Margin% (≥40 = elite SaaS)
    operating_leverage: Optional[float] = None  # Op Income Growth / Rev Growth ratio
    gross_margin_expansion: Optional[float] = None  # GM current - GM prior year (positive = improving)
    net_cash_position: Optional[float] = None  # Cash - Total Debt (positive = net cash)
    is_net_cash: bool = False             # Cash > Total Debt
    rd_to_revenue: Optional[float] = None # R&D Spend / Revenue (moat building signal)
    insider_net_buying: Optional[bool] = None  # Net insider purchases > 0 last 90d
    low_analyst_coverage: bool = False    # < 5 analysts = undiscovered gem
    revenue_per_employee: Optional[float] = None  # Asset-light efficiency metric

    # ── PRICE HISTORY ──────────────────────────────────────────────────────────
    price_history_20d: Optional[list[float]] = None  # Last 20 closing prices for sparkline

    # ── CHECKLIST BOOLEANS ────────────────────────────────────────────────────
    revenue_accelerating: bool = False
    earnings_positive: bool = False
    low_institutional_coverage: bool = False   # < 40% inst. ownership
    high_growth: bool = False                  # Revenue YoY > 20%
    profitable: bool = False                   # Net Margin > 0
    positive_fcf: bool = False                 # Free Cash Flow > 0
    low_debt: bool = False                     # Debt/Equity < 1.5


class ConfluenceItem(BaseModel):
    name: str
    passed: bool
    value: Optional[str] = None
    weight: float = 1.0


class AlphaScore(BaseModel):
    total: float = Field(..., ge=0.0, le=100.0)
    growth_score: float
    profitability_score: float
    moat_score: float
    health_score: float
    quality_rank: int = 50
    value_rank: int = 50
    grade: str                         # A+, A, B, C, D, F


class TickerValidation(BaseModel):
    ticker: str
    timestamp: str
    fundamentals: FundamentalResult
    confluence_checklist: list[ConfluenceItem]
    alpha_score: AlphaScore
    recommendation: str                # BUY, HOLD, SELL


class BubbleDataPoint(BaseModel):
    ticker: str
    company_name: str
    revenue_growth: float              # X axis (%)
    market_cap_billions: float         # Y axis (Billions USD)
    alpha_score: float
    sector: Optional[str]
    moat: Optional[str]


class AlertEvent(BaseModel):
    ticker: str
    alert_type: str                    
    message: str
    severity: str                      
    timestamp: str
    data: dict = {}


# ── FASE 1: Advanced Screener Filters ──────────────────────────────────────────
class ScreenerFilters(BaseModel):
    """User-defined filter parameters for advanced screener"""

    # ── VALUACIÓN ──────────────────────────────────────────────────────────────
    pe_min: Optional[float] = None
    pe_max: Optional[float] = 30.0
    ps_min: Optional[float] = None
    ps_max: Optional[float] = 3.0
    peg_min: Optional[float] = None
    peg_max: Optional[float] = 1.5
    ev_ebitda_min: Optional[float] = None
    ev_ebitda_max: Optional[float] = 15.0
    fcf_yield_min: Optional[float] = None

    # ── CRECIMIENTO ────────────────────────────────────────────────────────────
    revenue_growth_min: Optional[float] = 0.15      # 15% default
    earnings_growth_min: Optional[float] = 0.20     # 20% default
    revenue_cagr_3y_min: Optional[float] = 0.15
    fcf_growth_min: Optional[float] = None

    # ── RENTABILIDAD ───────────────────────────────────────────────────────────
    gross_margin_min: Optional[float] = 0.30        # 30% default
    operating_margin_min: Optional[float] = 0.10    # 10% default
    net_margin_min: Optional[float] = 0.05          # 5% default
    roe_min: Optional[float] = 0.15                 # 15% default
    roa_min: Optional[float] = 0.08                 # 8% default
    roic_min: Optional[float] = 0.12                # 12% default

    # ── BALANCE SHEET ──────────────────────────────────────────────────────────
    debt_to_equity_max: Optional[float] = 1.5
    debt_to_ebitda_max: Optional[float] = 2.0
    debt_to_fcf_max: Optional[float] = None
    current_ratio_min: Optional[float] = 1.5
    quick_ratio_min: Optional[float] = 1.0
    interest_coverage_min: Optional[float] = 5.0

    # ── LIQUIDEZ & TAMAÑO ──────────────────────────────────────────────────────
    market_cap_min: Optional[float] = 50e6          # $50M default
    market_cap_max: Optional[float] = 5e9           # $5B default
    avg_volume_min: Optional[float] = 100_000       # shares
    short_interest_max: Optional[float] = 0.20      # 20% default

    # ── CALIDAD ───────────────────────────────────────────────────────────────
    piotroski_f_score_min: Optional[float] = 6.0    # >6 = calidad
    altman_z_score_min: Optional[float] = None      # >3 = safe
    accruals_ratio_max: Optional[float] = None      # Low is better
    institutional_ownership_min: Optional[float] = 0.10
    institutional_ownership_max: Optional[float] = 0.50

    # ── GENERAL ────────────────────────────────────────────────────────────────
    alpha_score_min: Optional[float] = 50.0
    sectors: Optional[list[str]] = None             # Filter by sectors

    class Config:
        description = "Advanced screener filter parameters"


class MarketTapeItem(BaseModel):
    symbol: str
    price: float
    change: float
    percent: float
