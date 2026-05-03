"""
Alpha Station v4.0 — Pydantic data models
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class StageEnum(str, Enum):
    STAGE_1 = "Stage 1"           # Basing / accumulation
    STAGE_2 = "Stage 2"           # Advancing / breakout
    STAGE_3 = "Stage 3"           # Topping / distribution
    STAGE_4 = "Stage 4"           # Declining
    UNKNOWN = "Unknown"


class StageResult(BaseModel):
    stage: StageEnum
    confidence: float = Field(..., ge=0.0, le=1.0)
    ma50: float
    ma150: float
    ma200: float
    price: float
    price_vs_ma200_pct: float          # % above/below 200-day MA
    ma_alignment: bool                  # MA50 > MA150 > MA200
    price_above_all_mas: bool
    transitioning_to_2: bool           # Stage 1→2 signal
    stage_weeks: int                    # Weeks in current stage
    notes: list[str] = []


class GEXResult(BaseModel):
    ticker: str
    gex_total: float                   # Net GEX in dollars
    gex_call: float
    gex_put: float
    gex_flip_level: Optional[float]    # Price where GEX flips sign
    dominant_strikes: list[float]      # Top 3 gamma walls
    iv_rank: Optional[float]           # 0-100
    put_call_ratio: Optional[float]
    available: bool = True
    error: Optional[str] = None


class LiquidityResult(BaseModel):
    ticker: str
    rvol: float                        # Relative volume vs 20-day avg
    avg_volume_20d: float
    current_volume: float
    vwap: Optional[float]
    vwap_anchored: Optional[float]     # AVWAP from recent pivot
    stage2_alert: bool                 # RVOL > threshold AND Stage 2


class FundamentalResult(BaseModel):
    ticker: str
    company_name: str
    sector: Optional[str]
    industry: Optional[str]
    market_cap: Optional[float]
    revenue_growth_yoy: Optional[float]   # YoY %
    revenue_growth_qoq: Optional[float]   # QoQ %
    earnings_growth_yoy: Optional[float]
    gross_margin: Optional[float]
    net_margin: Optional[float]
    revenue_ttm: Optional[float]
    pe_ratio: Optional[float]
    ps_ratio: Optional[float]
    institutional_ownership_pct: Optional[float]
    short_float_pct: Optional[float]
    float_shares: Optional[float]
    # Checklist booleans
    revenue_accelerating: bool = False
    earnings_positive: bool = False
    low_institutional_coverage: bool = False   # < 40% inst. ownership = "Hidden Gem"
    high_growth: bool = False                  # Revenue YoY > 20%


class ConfluenceItem(BaseModel):
    name: str
    passed: bool
    value: Optional[str] = None
    weight: float = 1.0


class AlphaScore(BaseModel):
    total: float = Field(..., ge=0.0, le=100.0)
    stage_score: float
    gex_score: float
    rvol_score: float
    fundamental_score: float
    technical_score: float
    grade: str                         # A+, A, B, C, D, F


class TickerValidation(BaseModel):
    ticker: str
    timestamp: str
    stage: StageResult
    gex: GEXResult
    liquidity: LiquidityResult
    fundamentals: FundamentalResult
    confluence_checklist: list[ConfluenceItem]
    alpha_score: AlphaScore
    recommendation: str                # BUY_ZONE, WATCH, AVOID
    key_levels: dict[str, float] = {}  # support, resistance, gex_flip


class BubbleDataPoint(BaseModel):
    ticker: str
    company_name: str
    revenue_growth: float              # X axis
    gex_normalized: float              # Y axis
    rvol: float                        # Bubble size
    stage: str
    alpha_score: float
    sector: Optional[str]
    market_cap: Optional[float]
    stage2_alert: bool


class AlertEvent(BaseModel):
    ticker: str
    alert_type: str                    # "STAGE2_BREAKOUT", "RVOL_SPIKE", "GEX_FLIP"
    message: str
    severity: str                      # "HIGH", "MEDIUM", "LOW"
    timestamp: str
    data: dict = {}
