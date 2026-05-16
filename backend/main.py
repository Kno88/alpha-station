""" 
Alpha Station v6.0 — FastAPI Application Entry Point
Fundamental Analysis Only
"""

from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from loguru import logger

from config import settings
from models import (
    AlertEvent,
    AlphaScore,
    BubbleDataPoint,
    ConfluenceItem,
    ScreenerFilters,
    TickerValidation,
    MarketTapeItem,
)
from modules.alpha_scorer import build_recommendation, compute_alpha_score
from modules.fundamentals import FundamentalsEngine
from modules.pdf_generator import generate_report
import yfinance as yf

# ── App setup ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.pdf_output_dir, exist_ok=True)
    logger.info("Alpha Station v6.0 — Fundamental Engine online")
    yield
    logger.info("Alpha Station v6.0 — Fundamental Engine shutdown")

app = FastAPI(
    title="Alpha Station v6.0",
    description="Institutional-Grade Fundamental Analysis Engine",
    version="6.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
_fundamentals_engine = FundamentalsEngine()


# ── Core validation pipeline ──────────────────────────────────────────────────

async def _validate_ticker(ticker: str) -> TickerValidation:
    ticker = ticker.upper().strip()

    try:
        fund_result = await _fundamentals_engine.fetch(ticker)
    except Exception as exc:
        logger.error(f"Data fetch exception for {ticker}: {exc}")
        raise HTTPException(status_code=500, detail=f"Data fetch error: {exc}")

    if not fund_result:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no data available")

    # Alpha Score calculation
    alpha_score, confluence = compute_alpha_score(fund_result)
    recommendation = build_recommendation(alpha_score)

    return TickerValidation(
        ticker=ticker,
        timestamp=datetime.now(timezone.utc).isoformat(),
        fundamentals=fund_result,
        confluence_checklist=confluence,
        alpha_score=alpha_score,
        recommendation=recommendation,
    )


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "6.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/v1/validate/{ticker}", response_model=TickerValidation)
async def validate_ticker(ticker: str):
    """
    Full Alpha Station validation pipeline for a single ticker.
    Returns fundamentals and Alpha Score.
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
    Returns data for the Alpha Bubble Chart (Revenue Growth × Market Cap).
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()][:12]
    if not ticker_list:
        raise HTTPException(status_code=400, detail="No tickers provided")

    sem = asyncio.Semaphore(4)

    async def _single(t: str) -> Optional[BubbleDataPoint]:
        async with sem:
            try:
                v = await asyncio.wait_for(_validate_ticker(t), timeout=30)
                rev_growth = (v.fundamentals.revenue_growth_yoy or 0) * 100
                market_cap_b = (v.fundamentals.market_cap or 0) / 1e9
                return BubbleDataPoint(
                    ticker=t,
                    company_name=v.fundamentals.company_name,
                    revenue_growth=round(rev_growth, 1),
                    market_cap_billions=round(market_cap_b, 2),
                    alpha_score=v.alpha_score.total,
                    sector=v.fundamentals.sector,
                    moat=v.fundamentals.moat,
                )
            except asyncio.TimeoutError:
                logger.warning(f"Bubble data timeout for {t}")
                return None
            except Exception as e:
                logger.warning(f"Bubble data error for {t}: {e}")
                return None

    results = await asyncio.gather(*[_single(t) for t in ticker_list])
    return [r for r in results if r is not None]


@app.get("/api/v1/market-tape", response_model=list[MarketTapeItem])
async def get_market_tape():
    """
    Returns live market tape data for key indices.
    """
    symbols = ["SPY", "QQQ", "DIA", "IWM", "AAPL", "MSFT", "NVDA", "BTC-USD"]
    
    def _fetch():
        tickers = yf.Tickers(" ".join(symbols))
        data = []
        for sym in symbols:
            try:
                info = tickers.tickers[sym].info
                price = info.get("currentPrice") or info.get("regularMarketPrice") or 0.0
                prev = info.get("previousClose") or info.get("regularMarketPreviousClose") or price
                if price and prev:
                    change = price - prev
                    percent = (change / prev) * 100
                else:
                    change = 0.0
                    percent = 0.0
                data.append(MarketTapeItem(
                    symbol=sym.replace("-USD", ""),
                    price=price,
                    change=change,
                    percent=percent
                ))
            except Exception as e:
                logger.warning(f"Market tape error for {sym}: {e}")
        return data
        
    results = await asyncio.to_thread(_fetch)
    return results



@app.get("/api/v1/screener/hidden-gems", response_model=list[TickerValidation])
async def get_hidden_gems(
    tickers: str = Query(
        default="ASTS,IONQ,LUNR,RKLB,ACHR,JOBY,HLLY,AIOT,SMAR,BRZE",
        description="Small/mid cap universe to screen",
    )
):
    """
    Screen for Hidden Gems based on fundamental scores.
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
    valid = [r for r in results if isinstance(r, TickerValidation)]
    return sorted(valid, key=lambda g: g.alpha_score.total, reverse=True)


@app.post("/api/v1/screener/advanced", response_model=list[TickerValidation])
async def get_advanced_screener(
    tickers: str = Query(
        default="ASTS,IONQ,LUNR,RKLB,ACHR,JOBY,HLLY,AIOT,SMAR,BRZE,PLTR,NVDA,AXON,CELH,DUOL,MNDY",
        description="Universe of tickers to screen",
    ),
    filters: ScreenerFilters = None,
):
    """
    Advanced screener with comprehensive fundamental filters.
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()][:25]

    if not ticker_list:
        raise HTTPException(status_code=400, detail="No tickers provided")

    if filters is None:
        filters = ScreenerFilters()

    sem = asyncio.Semaphore(4)

    async def _safe(t: str):
        async with sem:
            try:
                return await asyncio.wait_for(_validate_ticker(t), timeout=30)
            except Exception as e:
                logger.warning(f"Screener error for {t}: {e}")
                return None

    results = await asyncio.gather(*[_safe(t) for t in ticker_list])
    valid = [r for r in results if isinstance(r, TickerValidation)]

    filtered = _apply_screener_filters(valid, filters)
    return sorted(filtered, key=lambda x: x.alpha_score.total, reverse=True)


def _apply_screener_filters(tickers: list[TickerValidation], filters: ScreenerFilters) -> list[TickerValidation]:
    """Apply fundamental filters to ticker list"""

    def passes_filter(t: TickerValidation) -> bool:
        f = t.fundamentals

        if filters.alpha_score_min is not None:
            if t.alpha_score.total < filters.alpha_score_min:
                return False

        if filters.pe_max is not None:
            if f.pe_ratio is None or f.pe_ratio > filters.pe_max:
                return False
        if filters.pe_min is not None:
            if f.pe_ratio is None or f.pe_ratio < filters.pe_min:
                return False
        if filters.ps_max is not None:
            if f.ps_ratio is None or f.ps_ratio > filters.ps_max:
                return False
        if filters.peg_max is not None:
            if f.peg_ratio is None or f.peg_ratio > filters.peg_max:
                return False
        if filters.ev_ebitda_max is not None:
            if f.ev_to_ebitda is None or f.ev_to_ebitda > filters.ev_ebitda_max:
                return False

        if filters.revenue_growth_min is not None:
            if f.revenue_growth_yoy is None or f.revenue_growth_yoy < filters.revenue_growth_min:
                return False
        if filters.earnings_growth_min is not None:
            if f.earnings_growth_yoy is None or f.earnings_growth_yoy < filters.earnings_growth_min:
                return False

        if filters.gross_margin_min is not None:
            if f.gross_margin is None or f.gross_margin < filters.gross_margin_min:
                return False
        if filters.operating_margin_min is not None:
            if f.operating_margin is None or f.operating_margin < filters.operating_margin_min:
                return False
        if filters.net_margin_min is not None:
            if f.net_margin is None or f.net_margin < filters.net_margin_min:
                return False
        if filters.roe_min is not None:
            if f.roe is None or f.roe < filters.roe_min:
                return False
        if filters.roa_min is not None:
            if f.roa is None or f.roa < filters.roa_min:
                return False

        if filters.debt_to_equity_max is not None:
            if f.debt_to_equity is None or f.debt_to_equity > filters.debt_to_equity_max:
                return False
        if filters.current_ratio_min is not None:
            if f.current_ratio is None or f.current_ratio < filters.current_ratio_min:
                return False
        if filters.quick_ratio_min is not None:
            if f.quick_ratio is None or f.quick_ratio < filters.quick_ratio_min:
                return False

        if filters.market_cap_min is not None:
            if f.market_cap is None or f.market_cap < filters.market_cap_min:
                return False
        if filters.market_cap_max is not None:
            if f.market_cap is None or f.market_cap > filters.market_cap_max:
                return False

        if filters.institutional_ownership_min is not None:
            if f.institutional_ownership_pct is None or f.institutional_ownership_pct < filters.institutional_ownership_min * 100:
                return False
        if filters.institutional_ownership_max is not None:
            if f.institutional_ownership_pct is None or f.institutional_ownership_pct > filters.institutional_ownership_max * 100:
                return False

        if filters.piotroski_f_score_min is not None:
            if f.piotroski_f_score is None or f.piotroski_f_score < filters.piotroski_f_score_min:
                return False
        if filters.altman_z_score_min is not None:
            if f.altman_z_score is None or f.altman_z_score < filters.altman_z_score_min:
                return False
        if filters.accruals_ratio_max is not None:
            if f.accruals_ratio is None or f.accruals_ratio > filters.accruals_ratio_max:
                return False
        if filters.fcf_yield_min is not None:
            if f.fcf_yield is None or f.fcf_yield < filters.fcf_yield_min:
                return False

        if filters.sectors is not None and len(filters.sectors) > 0:
            if f.sector not in filters.sectors:
                return False

        # ── Previously missing filters ────────────────────────────────────────
        if filters.ps_min is not None:
            if f.ps_ratio is None or f.ps_ratio < filters.ps_min:
                return False

        if filters.peg_min is not None:
            if f.peg_ratio is None or f.peg_ratio < filters.peg_min:
                return False

        if filters.ev_ebitda_min is not None:
            if f.ev_to_ebitda is None or f.ev_to_ebitda < filters.ev_ebitda_min:
                return False

        if filters.revenue_cagr_3y_min is not None:
            if f.revenue_cagr_3y is None or f.revenue_cagr_3y < filters.revenue_cagr_3y_min:
                return False

        if filters.fcf_growth_min is not None:
            if f.fcf_growth is None or f.fcf_growth < filters.fcf_growth_min:
                return False

        if filters.roic_min is not None:
            if f.roic is None or f.roic < filters.roic_min:
                return False

        if filters.debt_to_ebitda_max is not None:
            if f.debt_to_ebitda is None or f.debt_to_ebitda > filters.debt_to_ebitda_max:
                return False

        if filters.debt_to_fcf_max is not None:
            if f.debt_to_fcf is None or f.debt_to_fcf > filters.debt_to_fcf_max:
                return False

        if filters.interest_coverage_min is not None:
            if f.interest_coverage is None or f.interest_coverage < filters.interest_coverage_min:
                return False

        if filters.avg_volume_min is not None:
            if f.avg_volume_20d is None or f.avg_volume_20d < filters.avg_volume_min:
                return False

        if filters.short_interest_max is not None:
            # short_float_pct stored as % (e.g. 5.0), filter as decimal (e.g. 0.20 = 20%)
            if f.short_float_pct is None or f.short_float_pct > filters.short_interest_max * 100:
                return False

        return True

    return [t for t in tickers if passes_filter(t)]

