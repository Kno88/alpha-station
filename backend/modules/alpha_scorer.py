"""
Alpha Station v4.0 — Alpha Score Engine

Aggregates stage, fundamentals, RVOL, and technical signals into a 0-100 score.
Focus: Fundamentals-driven analysis (45%), Stage Analysis (30%), Liquidity (15%), Technical (10%).
"""

from __future__ import annotations

from models import (
    AlphaScore,
    ConfluenceItem,
    FundamentalResult,
    LiquidityResult,
    StageEnum,
    StageResult,
)
from config import settings


def compute_alpha_score(
    stage: StageResult,
    liquidity: LiquidityResult,
    fundamentals: FundamentalResult,
) -> tuple[AlphaScore, list[ConfluenceItem]]:
    """
    Returns AlphaScore (0-100) and a Confluence Checklist with pass/fail items.
    Focus: Stage Analysis + Fundamentals + Liquidity (RVOL).
    """

    checklist: list[ConfluenceItem] = []

    # ── Stage Score (0-30) ────────────────────────────────────────────────────
    stage_raw = _score_stage(stage, checklist)

    # ── Fundamental Score (0-45) ──────────────────────────────────────────────
    fund_raw = _score_fundamentals(fundamentals, checklist)

    # ── RVOL Score (0-15) ────────────────────────────────────────────────────
    rvol_raw = _score_rvol(liquidity, checklist)

    # ── Technical Score (0-10) ────────────────────────────────────────────────
    tech_raw = _score_technical(stage, liquidity, checklist)

    total = stage_raw + fund_raw + rvol_raw + tech_raw
    total = min(100.0, max(0.0, total))

    grade = _grade(total)

    return (
        AlphaScore(
            total=round(total, 1),
            stage_score=round(stage_raw, 1),
            rvol_score=round(rvol_raw, 1),
            fundamental_score=round(fund_raw, 1),
            technical_score=round(tech_raw, 1),
            grade=grade,
        ),
        checklist,
    )


# ── Scoring helpers ────────────────────────────────────────────────────────────

def _score_stage(stage: StageResult, checklist: list[ConfluenceItem]) -> float:
    max_pts = 30.0
    pts = 0.0

    is_s2 = stage.stage == StageEnum.STAGE_2
    checklist.append(ConfluenceItem(
        name="Stage 2 — Price advancing above all MAs",
        passed=is_s2,
        value=stage.stage.value,
        weight=3.0,
    ))
    if is_s2:
        pts += 14.0

    checklist.append(ConfluenceItem(
        name="MA Alignment (50 > 150 > 200)",
        passed=stage.ma_alignment,
        value="✓" if stage.ma_alignment else "✗",
        weight=2.0,
    ))
    if stage.ma_alignment:
        pts += 10.0

    checklist.append(ConfluenceItem(
        name="Price above all Moving Averages",
        passed=stage.price_above_all_mas,
        value="✓" if stage.price_above_all_mas else "✗",
        weight=2.0,
    ))
    if stage.price_above_all_mas:
        pts += 6.0

    return min(max_pts, pts)


def _score_rvol(liquidity: LiquidityResult, checklist: list[ConfluenceItem]) -> float:
    max_pts = 15.0
    rvol = liquidity.rvol

    checklist.append(ConfluenceItem(
        name=f"RVOL > {settings.rvol_threshold}x (Strong volume confirmation)",
        passed=rvol >= settings.rvol_threshold,
        value=f"{rvol:.2f}x",
        weight=2.0,
    ))

    # Continuous scoring: max at RVOL=5x
    pts = min(max_pts, (rvol / 5.0) * max_pts)
    return pts


def _score_fundamentals(fundamentals: FundamentalResult, checklist: list[ConfluenceItem]) -> float:
    max_pts = 45.0
    pts = 0.0

    # High Revenue Growth (≥ 20% YoY)
    checklist.append(ConfluenceItem(
        name="High Revenue Growth (≥ 20% YoY)",
        passed=fundamentals.high_growth,
        value=f"{fundamentals.revenue_growth_yoy * 100:.1f}%" if fundamentals.revenue_growth_yoy else "N/A",
        weight=3.0,
    ))
    if fundamentals.high_growth:
        pts += 15.0
    elif fundamentals.revenue_growth_yoy and fundamentals.revenue_growth_yoy > 0:
        pts += 7.0

    # Revenue Accelerating QoQ
    checklist.append(ConfluenceItem(
        name="Revenue Accelerating QoQ",
        passed=fundamentals.revenue_accelerating,
        value=f"{fundamentals.revenue_growth_qoq * 100:.1f}% QoQ" if fundamentals.revenue_growth_qoq else "N/A",
        weight=2.0,
    ))
    if fundamentals.revenue_accelerating:
        pts += 12.0

    # Positive Earnings / Net Margin
    checklist.append(ConfluenceItem(
        name="Positive Earnings / Net Margin",
        passed=fundamentals.earnings_positive,
        value=f"{fundamentals.net_margin * 100:.1f}%" if fundamentals.net_margin else "N/A",
        weight=1.5,
    ))
    if fundamentals.earnings_positive:
        pts += 10.0

    # Hidden Gem — Low Institutional Coverage (< 40%)
    checklist.append(ConfluenceItem(
        name="Hidden Gem — Low Institutional Coverage (< 40%)",
        passed=fundamentals.low_institutional_coverage,
        value=f"{fundamentals.institutional_ownership_pct:.1f}%" if fundamentals.institutional_ownership_pct else "N/A",
        weight=1.5,
    ))
    if fundamentals.low_institutional_coverage:
        pts += 8.0

    return min(max_pts, pts)


def _score_technical(
    stage: StageResult, liquidity: LiquidityResult, checklist: list[ConfluenceItem]
) -> float:
    max_pts = 10.0
    pts = 0.0

    # Stage 1→2 transition signal
    checklist.append(ConfluenceItem(
        name="Stage 1→2 Transition Signal (recent MA50 crossover)",
        passed=stage.transitioning_to_2,
        value="Active" if stage.transitioning_to_2 else "—",
        weight=2.5,
    ))
    if stage.transitioning_to_2:
        pts += 5.0

    # Price extended less than 20% above MA200 (healthy, not overextended)
    healthy_extension = 0 <= stage.price_vs_ma200_pct <= 20
    checklist.append(ConfluenceItem(
        name="Healthy MA200 Extension (0–20% above)",
        passed=healthy_extension,
        value=f"+{stage.price_vs_ma200_pct:.1f}%",
        weight=1.0,
    ))
    if healthy_extension:
        pts += 5.0
    elif 0 <= stage.price_vs_ma200_pct <= 35:
        pts += 2.0

    return min(max_pts, pts)


def _grade(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B+"
    if score >= 60:
        return "B"
    if score >= 50:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def build_recommendation(score: AlphaScore, stage: StageResult) -> str:
    if stage.stage == StageEnum.STAGE_4:
        return "AVOID"
    if score.total >= 70 and stage.stage == StageEnum.STAGE_2:
        return "BUY_ZONE"
    if score.total >= 50:
        return "WATCH"
    return "AVOID"
