"""
Alpha Station v6.0 — Fundamental Alpha Score Engine
Institutional-grade scoring based purely on fundamentals, market share, and moat.
"""

from __future__ import annotations

from typing import Optional

from models import (
    AlphaScore,
    ConfluenceItem,
    FundamentalResult,
)

def compute_alpha_score(
    fundamentals: FundamentalResult,
) -> tuple[AlphaScore, list[ConfluenceItem]]:
    """
    Returns AlphaScore (0-100) based entirely on fundamental metrics, 
    and a Confluence Checklist.
    """

    checklist: list[ConfluenceItem] = []

    # ── Growth Score (0-30) ──────────────────────────────────────────────────
    growth_raw = _score_growth(fundamentals, checklist)

    # ── Profitability Score (0-30) ───────────────────────────────────────────
    profit_raw = _score_profitability(fundamentals, checklist)

    # ── Moat & Market Share Score (0-20) ─────────────────────────────────────
    moat_raw = _score_moat(fundamentals, checklist)

    # ── Health & Quality Score (0-20) ────────────────────────────────────────
    health_raw = _score_health(fundamentals, checklist)

    total = growth_raw + profit_raw + moat_raw + health_raw
    total = min(100.0, max(0.0, total))

    grade = _grade(total)

    quality_rank = _calculate_quality_rank(fundamentals)
    value_rank = _calculate_value_rank(fundamentals)

    return (
        AlphaScore(
            total=round(total, 1),
            growth_score=round(growth_raw, 1),
            profitability_score=round(profit_raw, 1),
            moat_score=round(moat_raw, 1),
            health_score=round(health_raw, 1),
            quality_rank=quality_rank,
            value_rank=value_rank,
            grade=grade,
        ),
        checklist,
    )


def _score_growth(f: FundamentalResult, checklist: list[ConfluenceItem]) -> float:
    max_pts = 30.0
    pts = 0.0

    # Revenue Growth >= 20% (sector-agnostic growth signal)
    high_growth = f.revenue_growth_yoy is not None and f.revenue_growth_yoy >= 0.20
    checklist.append(ConfluenceItem(
        name="High Revenue Growth (≥ 20% YoY)",
        passed=high_growth,
        value=f"{f.revenue_growth_yoy * 100:.1f}%" if f.revenue_growth_yoy is not None else "N/A",
        weight=2.0,
    ))
    if high_growth:
        pts += 10.0
    elif f.revenue_growth_yoy is not None and f.revenue_growth_yoy > 0.10:
        pts += 5.0

    # Rule of 40 — institutional quality filter for growth companies
    # Rewards companies growing fast AND generating cash, regardless of margins alone
    rule40_passed = f.rule_of_40 is not None and f.rule_of_40 >= 40
    checklist.append(ConfluenceItem(
        name="Rule of 40 (Rev Growth% + FCF Margin% ≥ 40)",
        passed=rule40_passed,
        value=f"{f.rule_of_40:.1f}" if f.rule_of_40 is not None else "N/A",
        weight=2.5,
    ))
    if rule40_passed:
        pts += 10.0
    elif f.rule_of_40 is not None and f.rule_of_40 >= 25:
        pts += 5.0

    # Operating Leverage > 1 — margins expanding faster than revenue
    op_lev_passed = f.operating_leverage is not None and f.operating_leverage > 1.0
    checklist.append(ConfluenceItem(
        name="Operating Leverage > 1x (Margin Expansion)",
        passed=op_lev_passed,
        value=f"{f.operating_leverage:.2f}x" if f.operating_leverage is not None else "N/A",
        weight=1.5,
    ))
    if op_lev_passed:
        pts += 10.0
    elif f.operating_leverage is not None and f.operating_leverage > 0:
        pts += 4.0

    # Earnings Growth >= 15%
    earnings_growth = f.earnings_growth_yoy is not None and f.earnings_growth_yoy >= 0.15
    checklist.append(ConfluenceItem(
        name="Earnings Growth (≥ 15% YoY)",
        passed=earnings_growth,
        value=f"{f.earnings_growth_yoy * 100:.1f}%" if f.earnings_growth_yoy is not None else "N/A",
        weight=1.5,
    ))
    # Contributes up to max_pts cap
    if earnings_growth:
        pts += 5.0

    return min(max_pts, pts)


def _score_profitability(f: FundamentalResult, checklist: list[ConfluenceItem]) -> float:
    max_pts = 30.0
    pts = 0.0

    # Net Margin >= 5% (not 10% — avoids penalizing good businesses in low-margin sectors)
    # Context: retail 2-5%, SaaS 20-30%, banks 15-25%, manufacturing 5-10%
    high_margin = f.net_margin is not None and f.net_margin >= 0.05
    elite_margin = f.net_margin is not None and f.net_margin >= 0.15
    checklist.append(ConfluenceItem(
        name="Healthy Net Margin (≥ 5%)",
        passed=high_margin,
        value=f"{f.net_margin * 100:.1f}%" if f.net_margin is not None else "N/A",
        weight=2.0,
    ))
    if elite_margin:
        pts += 12.0
    elif high_margin:
        pts += 8.0
    elif f.net_margin is not None and f.net_margin > 0:
        pts += 4.0

    # Gross Margin Expansion — sector-relative quality signal
    # A company improving its gross margin is improving pricing power or COGS efficiency
    gm_exp_passed = f.gross_margin_expansion is not None and f.gross_margin_expansion > 0
    checklist.append(ConfluenceItem(
        name="Gross Margin Expanding (YoY)",
        passed=gm_exp_passed,
        value=f"{f.gross_margin_expansion * 100:+.1f}pp" if f.gross_margin_expansion is not None else "N/A",
        weight=1.5,
    ))
    if gm_exp_passed:
        pts += 8.0

    # ROE >= 15%
    high_roe = f.roe is not None and f.roe >= 0.15
    checklist.append(ConfluenceItem(
        name="Return on Equity (≥ 15%)",
        passed=high_roe,
        value=f"{f.roe * 100:.1f}%" if f.roe is not None else "N/A",
        weight=2.0,
    ))
    if high_roe:
        pts += 10.0
    elif f.roe is not None and f.roe > 0.05:
        pts += 4.0

    return min(max_pts, pts)


def _score_moat(f: FundamentalResult, checklist: list[ConfluenceItem]) -> float:
    max_pts = 20.0
    pts = 0.0

    # Moat Rating
    has_moat = f.moat in ["Wide", "Narrow"]
    checklist.append(ConfluenceItem(
        name="Economic Moat",
        passed=has_moat,
        value=f.moat,
        weight=3.0,
    ))
    if f.moat == "Wide":
        pts += 8.0
    elif f.moat == "Narrow":
        pts += 4.0

    # R&D Intensity (>10% = moat-building signal, esp. tech/pharma/biotech)
    rd_passed = f.rd_to_revenue is not None and f.rd_to_revenue >= 0.10
    checklist.append(ConfluenceItem(
        name="High R&D Intensity (≥ 10% of Revenue)",
        passed=rd_passed,
        value=f"{f.rd_to_revenue * 100:.1f}%" if f.rd_to_revenue is not None else "N/A",
        weight=1.5,
    ))
    if rd_passed:
        pts += 6.0
    elif f.rd_to_revenue is not None and f.rd_to_revenue >= 0.05:
        pts += 3.0

    # Asset-Light Efficiency (Revenue per Employee > $500K)
    rev_per_emp_passed = f.revenue_per_employee is not None and f.revenue_per_employee >= 500_000
    checklist.append(ConfluenceItem(
        name="Asset-Light Model (Rev/Employee ≥ $500K)",
        passed=rev_per_emp_passed,
        value=f"${f.revenue_per_employee/1000:.0f}K" if f.revenue_per_employee is not None else "N/A",
        weight=1.0,
    ))
    if rev_per_emp_passed:
        pts += 6.0
    elif f.revenue_per_employee is not None and f.revenue_per_employee >= 300_000:
        pts += 3.0

    return min(max_pts, pts)


def _score_health(f: FundamentalResult, checklist: list[ConfluenceItem]) -> float:
    max_pts = 20.0
    pts = 0.0

    # Net Cash Position (cash > debt = fortress balance sheet)
    net_cash_passed = f.is_net_cash
    checklist.append(ConfluenceItem(
        name="Net Cash Position (Cash > Total Debt)",
        passed=net_cash_passed,
        value=f"${f.net_cash_position/1e9:.2f}B" if f.net_cash_position is not None else "N/A",
        weight=2.0,
    ))
    if net_cash_passed:
        pts += 8.0
    elif f.debt_to_equity is not None and f.debt_to_equity < 1.0:
        pts += 4.0  # partial credit for low debt

    # Piotroski F-Score >= 7
    high_pio = f.piotroski_f_score is not None and f.piotroski_f_score >= 7
    checklist.append(ConfluenceItem(
        name="High Quality Earnings (Piotroski ≥ 7)",
        passed=high_pio,
        value=f"{int(f.piotroski_f_score)}/9" if f.piotroski_f_score is not None else "N/A",
        weight=1.5,
    ))
    if high_pio:
        pts += 8.0
    elif f.piotroski_f_score is not None and f.piotroski_f_score >= 5:
        pts += 4.0

    # Low Analyst Coverage (< 5 analysts) — undiscovered gem signal
    checklist.append(ConfluenceItem(
        name="Low Analyst Coverage (< 5 analysts)",
        passed=f.low_analyst_coverage,
        value="Undiscovered" if f.low_analyst_coverage else "Covered",
        weight=0.5,
    ))
    if f.low_analyst_coverage:
        pts += 4.0

    return min(max_pts, pts)


def _calculate_quality_rank(f: FundamentalResult) -> int:
    score = 50
    if f.piotroski_f_score is not None:
        score += (f.piotroski_f_score - 5) * 5
    if f.net_margin is not None and f.net_margin > 0.1:
        score += 10
    if f.roe is not None and f.roe > 0.15:
        score += 10
    if f.debt_to_equity is not None and f.debt_to_equity < 1.0:
        score += 10
    if f.altman_z_score is not None and f.altman_z_score >= 3.0:
        score += 10
    return int(min(99, max(1, score)))


def _calculate_value_rank(f: FundamentalResult) -> int:
    score = 50
    if f.fcf_yield is not None:
        if f.fcf_yield >= 0.05: score += 20
        elif f.fcf_yield >= 0.03: score += 10
    if f.pe_ratio is not None and f.pe_ratio > 0:
        if f.pe_ratio < 15: score += 15
        elif f.pe_ratio < 25: score += 5
        elif f.pe_ratio > 50: score -= 15
    if f.ps_ratio is not None and f.ps_ratio > 0:
        if f.ps_ratio < 2: score += 10
        elif f.ps_ratio > 10: score -= 10
    return int(min(99, max(1, score)))


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


def build_recommendation(score: AlphaScore) -> str:
    """Build recommendation strictly on fundamentals."""
    if score.total >= 75:
        return "STRONG_BUY"
    if score.total >= 60:
        return "BUY"
    if score.total >= 40:
        return "HOLD"
    return "AVOID"
