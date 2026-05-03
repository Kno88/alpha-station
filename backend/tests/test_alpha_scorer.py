"""
Unit tests for Alpha Score Engine.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from modules.alpha_scorer import compute_alpha_score, build_recommendation
from models import (
    StageResult, StageEnum, GEXResult, LiquidityResult, FundamentalResult
)


def _stage2() -> StageResult:
    return StageResult(
        stage=StageEnum.STAGE_2, confidence=0.9, ma50=150, ma150=140,
        ma200=130, price=160, price_vs_ma200_pct=23.0,
        ma_alignment=True, price_above_all_mas=True,
        transitioning_to_2=True, stage_weeks=5,
    )


def _gex_positive() -> GEXResult:
    return GEXResult(
        ticker="TEST", gex_total=500_000_000, gex_call=600_000_000,
        gex_put=-100_000_000, gex_flip_level=155.0,
        dominant_strikes=[148.0, 150.0, 155.0],
        iv_rank=30, put_call_ratio=0.6, available=True,
    )


def _liquidity_high_rvol() -> LiquidityResult:
    return LiquidityResult(
        ticker="TEST", rvol=3.2, avg_volume_20d=1_000_000,
        current_volume=3_200_000, vwap=158.0, vwap_anchored=155.0,
        stage2_alert=True,
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
    )


class TestAlphaScorer:
    def test_high_quality_ticker_scores_above_70(self):
        score, checklist = compute_alpha_score(
            _stage2(), _gex_positive(), _liquidity_high_rvol(), _fundamentals_high_growth()
        )
        assert score.total >= 70, f"Expected >= 70, got {score.total}"

    def test_grade_a_for_high_score(self):
        score, _ = compute_alpha_score(
            _stage2(), _gex_positive(), _liquidity_high_rvol(), _fundamentals_high_growth()
        )
        assert score.grade in ("A+", "A", "B+")

    def test_score_components_sum_roughly_to_total(self):
        score, _ = compute_alpha_score(
            _stage2(), _gex_positive(), _liquidity_high_rvol(), _fundamentals_high_growth()
        )
        component_sum = (
            score.stage_score + score.gex_score + score.rvol_score
            + score.fundamental_score + score.technical_score
        )
        assert abs(component_sum - score.total) < 2.0, f"Sum mismatch: {component_sum} vs {score.total}"

    def test_checklist_has_items(self):
        _, checklist = compute_alpha_score(
            _stage2(), _gex_positive(), _liquidity_high_rvol(), _fundamentals_high_growth()
        )
        assert len(checklist) >= 8

    def test_recommendation_buy_zone_for_high_score(self):
        score, _ = compute_alpha_score(
            _stage2(), _gex_positive(), _liquidity_high_rvol(), _fundamentals_high_growth()
        )
        rec = build_recommendation(score, _stage2())
        assert rec == "BUY_ZONE"

    def test_stage4_always_avoid(self):
        stage4 = StageResult(
            stage=StageEnum.STAGE_4, confidence=0.8, ma50=100, ma150=110,
            ma200=120, price=90, price_vs_ma200_pct=-25.0,
            ma_alignment=False, price_above_all_mas=False,
            transitioning_to_2=False, stage_weeks=8,
        )
        score, _ = compute_alpha_score(
            stage4, _gex_positive(), _liquidity_high_rvol(), _fundamentals_high_growth()
        )
        rec = build_recommendation(score, stage4)
        assert rec == "AVOID"
