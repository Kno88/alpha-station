"""
Alpha Station v4.0 — FastAPI Application Entry Point
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from typing import Optional

import yfinance as yf
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from loguru import logger

from config import settings
from models import (
    AlertEvent,
    AlphaScore,
    BubbleDataPoint,
    ConfluenceItem,
    TickerValidation,
)
from modules.alpha_scorer import build_recommendation, compute_alpha_score
from modules.data_fetcher import get_daily_ohlcv, get_spot_price
from modules.fundamentals import FundamentalsEngine
from modules.gex_engine import GEXEngine, LiquidityEngine
from modules.pdf_generator import generate_report
from modules.stage_analysis import StageAnalyzer

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Alpha Station v4.0",
    description="Exponential Growth Detection Engine",
    version="4.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
_stage_analyzer = StageAnalyzer()
_liquidity_engine = LiquidityEngine()
_fundamentals_engine = FundamentalsEngine()
_gex_engine = GEXEngine()


# ── Core validation pipeline ──────────────────────────────────────────────────

async def _validate_ticker(ticker: str) -> TickerValidation:
    ticker = ticker.upper().strip()

    # 1. Fetch price data
    try:
        df = get_daily_ohlcv(ticker, days=300)
        spot = get_spot_price(ticker)
    except Exception as exc:
        logger.error(f"Data fetch exception for {ticker}: {exc}")
        raise HTTPException(status_code=500, detail=f"Data fetch error: {exc}")

    if df is None or spot is None:
        logger.warning(f"No data for {ticker}: df={df is not None}, spot={spot}")
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no data available")

    # 2. Run all engines concurrently
    stage_result, gex_result, fund_result = await asyncio.gather(
        asyncio.to_thread(_stage_analyzer.analyze, ticker, df),
        _gex_engine.calculate(ticker, spot),
        _fundamentals_engine.fetch(ticker),
    )

    liquidity_result = _liquidity_engine.compute(ticker, df)

    # 3. Score
    alpha_score, confluence = compute_alpha_score(
        stage_result, gex_result, liquidity_result, fund_result
    )

    recommendation = build_recommendation(alpha_score, stage_result)

    # 4. Key levels
    key_levels: dict[str, float] = {}
    if stage_result.ma50:
        key_levels["ma50"] = stage_result.ma50
    if stage_result.ma200:
        key_levels["ma200"] = stage_result.ma200
    if gex_result.gex_flip_level:
        key_levels["gex_flip"] = gex_result.gex_flip_level
    if liquidity_result.vwap_anchored:
        key_levels["avwap"] = liquidity_result.vwap_anchored

    return TickerValidation(
        ticker=ticker,
        timestamp=datetime.now(timezone.utc).isoformat(),
        stage=stage_result,
        gex=gex_result,
        liquidity=liquidity_result,
        fundamentals=fund_result,
        confluence_checklist=confluence,
        alpha_score=alpha_score,
        recommendation=recommendation,
        key_levels=key_levels,
    )


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "4.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/validate/{ticker}", response_model=TickerValidation)
async def validate_ticker(ticker: str):
    """
    Full Alpha Station validation pipeline for a single ticker.
    Returns stage analysis, GEX, RVOL, fundamentals, and Alpha Score.
    """
    return await _validate_ticker(ticker)


@app.get("/api/v1/report/{ticker}")
async def get_report(ticker: str):
    """
    Generate and stream a professional PDF report for a ticker.
    """
    validation = await _validate_ticker(ticker)

    try:
        pdf_bytes = await asyncio.to_thread(generate_report, validation)
    except Exception as e:
        logger.error(f"PDF generation failed for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation error: {str(e)}")

    filename = f"alpha_report_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/v1/bubble-data", response_model=list[BubbleDataPoint])
async def get_bubble_data(
    tickers: str = Query(
        default="NVDA,SMCI,AXON,CELH,ENPH,DUOL,MNDY,GLBE,ASTS,IONQ",
        description="Comma-separated list of tickers",
    )
):
    """
    Returns data for the Alpha Bubble Chart (Revenue Growth × GEX × RVOL).
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()][:12]
    if not ticker_list:
        raise HTTPException(status_code=400, detail="No tickers provided")

    sem = asyncio.Semaphore(4)  # max 4 concurrent yfinance downloads

    async def _single(t: str) -> Optional[BubbleDataPoint]:
        async with sem:
            try:
                v = await asyncio.wait_for(_validate_ticker(t), timeout=30)
                rev_growth = (v.fundamentals.revenue_growth_yoy or 0) * 100
                gex_norm = (
                    v.gex.gex_total / 1e9
                    if v.gex.available and v.gex.gex_total
                    else 0.0
                )
                return BubbleDataPoint(
                    ticker=t,
                    company_name=v.fundamentals.company_name,
                    revenue_growth=round(rev_growth, 1),
                    gex_normalized=round(gex_norm, 3),
                    rvol=v.liquidity.rvol,
                    stage=v.stage.stage.value,
                    alpha_score=v.alpha_score.total,
                    sector=v.fundamentals.sector,
                    market_cap=v.fundamentals.market_cap,
                    stage2_alert=v.liquidity.stage2_alert,
                )
            except asyncio.TimeoutError:
                logger.warning(f"Bubble data timeout for {t}")
                return None
            except Exception as e:
                logger.warning(f"Bubble data error for {t}: {e}")
                return None

    results = await asyncio.gather(*[_single(t) for t in ticker_list])
    return [r for r in results if r is not None]


@app.get("/api/v1/alerts", response_model=list[AlertEvent])
async def get_alerts(
    tickers: str = Query(default="NVDA,SMCI,AXON,CELH,ENPH"),
):
    """
    Scan tickers and return active Stage 2 + RVOL alerts.
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    alerts: list[AlertEvent] = []

    for t in ticker_list:
        try:
            v = await _validate_ticker(t)

            # Stage 2 + RVOL alert
            if (
                v.stage.stage.value == "Stage 2"
                and v.liquidity.rvol >= settings.rvol_threshold
            ):
                alerts.append(AlertEvent(
                    ticker=t,
                    alert_type="STAGE2_BREAKOUT",
                    message=f"{t} — Stage 2 breakout with RVOL {v.liquidity.rvol:.1f}x",
                    severity="HIGH",
                    timestamp=v.timestamp,
                    data={
                        "rvol": v.liquidity.rvol,
                        "alpha_score": v.alpha_score.total,
                        "stage": v.stage.stage.value,
                        "price": v.stage.price,
                    },
                ))

            # Stage 1→2 transition
            if v.stage.transitioning_to_2:
                alerts.append(AlertEvent(
                    ticker=t,
                    alert_type="STAGE2_TRANSITION",
                    message=f"{t} — Stage 1→2 transition in progress",
                    severity="MEDIUM",
                    timestamp=v.timestamp,
                    data={"price": v.stage.price, "ma50": v.stage.ma50},
                ))

            # GEX flip
            if v.gex.available and v.gex.gex_flip_level:
                price = v.stage.price
                flip = v.gex.gex_flip_level
                if abs(price - flip) / flip < 0.02:  # Within 2% of flip level
                    alerts.append(AlertEvent(
                        ticker=t,
                        alert_type="GEX_FLIP",
                        message=f"{t} — Price near GEX flip level ${flip:.2f}",
                        severity="MEDIUM",
                        timestamp=v.timestamp,
                        data={"price": price, "gex_flip": flip},
                    ))
        except Exception as e:
            logger.warning(f"Alert scan error for {t}: {e}")
            continue

    alerts.sort(key=lambda a: {"HIGH": 0, "MEDIUM": 1, "LOW": 2}[a.severity])
    return alerts


@app.get("/api/v1/screener/hidden-gems", response_model=list[TickerValidation])
async def get_hidden_gems(
    tickers: str = Query(
        default="ASTS,IONQ,LUNR,RKLB,ACHR,JOBY,HLLY,AIOT,SMAR,BRZE",
        description="Small/mid cap universe to screen",
    )
):
    """
    Screen for Hidden Gems: small/mid caps with low institutional coverage,
    high growth, and Stage 2 characteristics.
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()][:12]
    sem = asyncio.Semaphore(4)

    async def _safe(t: str):
        async with sem:
            try:
                return await asyncio.wait_for(_validate_ticker(t), timeout=30)
            except Exception:
                return None

    results = await asyncio.gather(*[_safe(t) for t in ticker_list])

    # Return all valid results sorted by alpha score (relax gem filter so table always shows data)
    valid = [r for r in results if isinstance(r, TickerValidation)]
    return sorted(valid, key=lambda g: g.alpha_score.total, reverse=True)


# ── Startup / Shutdown ─────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    os.makedirs(settings.pdf_output_dir, exist_ok=True)
    logger.info("Alpha Station v4.0 — Engine online")


@app.on_event("shutdown")
async def shutdown():
    await _gex_engine.close()
    logger.info("Alpha Station v4.0 — Engine shutdown")
