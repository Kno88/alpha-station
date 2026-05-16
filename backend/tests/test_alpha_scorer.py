"""
Unit tests for Alpha Score Engine v5.0
Run with: py -m pytest tests/ -v
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from modules.alpha_scorer import compute_alpha_score, build_recommendation
from models import (
    StageResult, StageEnum, LiquidityResult, FundamentalResult, RSLineResult
)


def _stage2() -> StageResult:
    return StageResult(
        stage=StageEnum.STAGE_2, confidence=0.9, ma50=150, ma150=140,
        ma200=130, price=160, price_vs_ma200_pct=23.0,
        ma_alignment=True, price_above_all_mas=True,
        transitioning_to_2=True, stage_weeks=5,
        vcp_detected=True, vcp_tightness=0.7, base_count=1,
        base_depth_pct=12.0, high_52w=165, low_52w=90,
    )


def _stage4() -> StageResult:
    return StageResult(
        stage=StageEnum.STAGE_4, confidence=0.8, ma50=100, ma150=110,
        ma200=120, price=90, price_vs_ma200_pct=-25.0,
        ma_alignment=False, price_above_all_mas=False,
        transitioning_to_2=False, stage_weeks=8,
    )


def _liquidity_high_rvol() -> LiquidityResult:
    return LiquidityResult(
        ticker="TEST", rvol=3.2, avg_volume_20d=1_000_000,
        current_volume=3_200_000, vwap=158.0, vwap_anchored=155.0,
        stage2_alert=True,
        up_down_volume_ratio=1.8, volume_dry_up=True, pocket_pivot=True,
        ad_rating="B",
    )


def _fundamentals_high_growth() -> FundamentalResult:
    return FundamentalResult(
        ticker="TEST", company_name="Test Corp",
        sector="Technology", industry="Software",
        market_cap=5_000_000_000, revenue_growth_yoy=0.45,
        revenue_growth_qoq=0.12, earnings_growth_yoy=0.30,
        gross_margin=0.72, net_margin=0.15, revenue_ttm=800_000_000,
        pe_ratio=35.0, ps_ratio=6.0, institutional_ownership_pct=28.0,
        short_float_pct=4.0, float_shares=100_000_000,
        revenue_accelerating=True, earnings_positive=True,
        low_institutional_coverage=True, high_growth=True,
        # Optional fields required by Pydantic
        peg_ratio=1.2, ev_to_ebitda=18.0, price_to_book=8.0,
        forward_pe=30.0, revenue_cagr_3y=0.35,
        earnings_growth_qoq=None, fcf_growth=0.2,
        operating_margin=0.18, fcf_margin=0.12,
        roe=0.25, roa=0.12, roic=0.20,
        total_debt=500_000_000, total_equity=2_000_000_000,
        total_assets=3_000_000_000, cash_and_equiv=800_000_000,
        debt_to_equity=0.25, debt_to_ebitda=1.5,
        current_ratio=2.5, quick_ratio=2.0, interest_coverage=15.0,
        piotroski_f_score=7, altman_z_score=4.5, accruals_ratio=None,
        insider_ownership_pct=5.0, insider_buying_6m=True,
        positive_fcf=True, earnings_surprise_pct=8.0,
        net_debt=None, avg_volume_20d=1_000_000, current_volume=3_200_000,
        fcf_to_net_income=None, fcf_yield=0.08, earnings_yield=0.05,
        capex_to_revenue=0.05, debt_to_fcf=1.5,
    )


def _rs_strong() -> RSLineResult:
    return RSLineResult(
        ticker="TEST", rs_line=1.5, rs_rating=88,
        rs_line_new_high=True, rs_line_near_high=True,
        rs_line_slope=0.005, rs_line_ma20=1.45,
        rs_line_above_ma=True, rs_divergence_bullish=False,
        rs_rank=1, rs_percentile_63d=90, rs_percentile_126d=85,
        rs_percentile_252d=80,
    )


def _rs_weak() -> RSLineResult:
    return RSLineResult(
        ticker="TEST", rs_line=0.8, rs_rating=25,
        rs_line_new_high=False, rs_line_near_high=False,
        rs_line_slope=-0.003, rs_line_ma20=0.85,
        rs_line_above_ma=False, rs_divergence_bullish=False,
        rs_rank=10,
    )


class TestAlphaScorer:
    def test_high_quality_ticker_scores_above_70(self):
        score, checklist = compute_alpha_score(
            _stage2(), _liquidity_high_rvol(), _fundamentals_high_growth(), _rs_strong()
        )
        assert score.total >= 70, f"Expected >= 70, got {score.total}"

    def test_grade_a_for_high_score(self):
        score, _ = compute_alpha_score(
            _stage2(), _liquidity_high_rvol(), _fundamentals_high_growth(), _rs_strong()
        )
        assert score.grade in ("A+", "A", "B+")

    def test_score_components_sum_roughly_to_total(self):
        score, _ = compute_alpha_score(
            _stage2(), _liquidity_high_rvol(), _fundamentals_high_growth(), _rs_strong()
        )
        component_sum = (
            score.stage_score + score.rvol_score
            + score.fundamental_score + score.rs_score
        )
        assert abs(component_sum - score.total) < 2.0, f"Sum mismatch: {component_sum} vs {score.total}"

    def test_checklist_has_items(self):
        _, checklist = compute_alpha_score(
            _stage2(), _liquidity_high_rvol(), _fundamentals_high_growth(), _rs_strong()
        )
        assert len(checklist) >= 10

    def test_recommendation_buy_zone_for_high_score(self):
        score, _ = compute_alpha_score(
            _stage2(), _liquidity_high_rvol(), _fundamentals_high_growth(), _rs_strong()
        )
        rec = build_recommendation(score, _stage2())
        assert rec == "BUY_ZONE"

    def test_stage4_always_avoid(self):
        score, _ = compute_alpha_score(
            _stage4(), _liquidity_high_rvol(), _fundamentals_high_growth(), _rs_strong()
        )
        rec = build_recommendation(score, _stage4())
        assert rec == "AVOID"

    def test_weak_rs_lowers_score(self):
        strong_score, _ = compute_alpha_score(
            _stage2(), _liquidity_high_rvol(), _fundamentals_high_growth(), _rs_strong()
        )
        weak_score, _ = compute_alpha_score(
            _stage2(), _liquidity_high_rvol(), _fundamentals_high_growth(), _rs_weak()
        )
        assert strong_score.total > weak_score.total, "Strong RS should give higher score"

    def test_no_rs_line_still_works(self):
        """Backward compat: score works without RS Line."""
        score, checklist = compute_alpha_score(
            _stage2(), _liquidity_high_rvol(), _fundamentals_high_growth(), None
        )
        assert 0 <= score.total <= 100
        assert len(checklist) >= 5
