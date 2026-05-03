"""
Alpha Station v4.0 — PDF Report Generator

Generates a professional institutional-grade PDF report using ReportLab.
Design: Dark Mode Institutional palette (Oxford Grey + Neon Green + Electric Blue)
"""

from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Optional

import yfinance as yf
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    Image,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, PolyLine
from reportlab.graphics.charts.lineplots import LinePlot
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas as pdfcanvas

from config import settings
from models import TickerValidation

# ── Institutional Dark Palette ────────────────────────────────────────────────
OXFORD_GREY = colors.HexColor("#1C2333")       # Background
CARD_BG = colors.HexColor("#242E42")            # Card background
BORDER = colors.HexColor("#2D3A52")             # Card border
NEON_GREEN = colors.HexColor("#00FF87")         # Positive / bullish
ELECTRIC_BLUE = colors.HexColor("#0088FF")      # Neutral / info
AMBER = colors.HexColor("#FFB800")              # Warning
RED = colors.HexColor("#FF4560")                # Negative / bearish
WHITE = colors.HexColor("#E8EBF0")
MUTED = colors.HexColor("#6B7A99")
GOLD = colors.HexColor("#F59E0B")


def generate_report(validation: TickerValidation) -> bytes:
    """Generate a PDF report and return raw bytes."""
    buf = io.BytesIO()

    # Page setup
    doc = BaseDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="main",
    )

    def _dark_background(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(OXFORD_GREY)
        canvas.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
        canvas.restoreState()

    template = PageTemplate(id="dark", frames=[frame], onPage=_dark_background)
    doc.addPageTemplates([template])

    story = []
    story += _build_header(validation)
    story += _build_alpha_score_banner(validation)
    story += _build_stage_section(validation)
    story += _build_confluence_checklist(validation)
    story += _build_gex_section(validation)
    story += _build_fundamentals_section(validation)
    story += _build_price_trend_chart(validation)
    story += _build_footer(validation)

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Section builders ──────────────────────────────────────────────────────────

def _build_header(v: TickerValidation) -> list:
    s = _styles()
    ts = datetime.fromisoformat(v.timestamp).strftime("%B %d, %Y  %H:%M UTC")

    elements = [
        Paragraph(
            f'<font color="{ELECTRIC_BLUE.hexval()}">■</font> ALPHA STATION v4.0',
            s["brand"],
        ),
        Paragraph(
            f'<font color="{WHITE.hexval()}">TECHNICAL INTELLIGENCE REPORT</font>',
            s["report_subtitle"],
        ),
        Spacer(1, 4 * mm),
        HRFlowable(width="100%", thickness=1, color=ELECTRIC_BLUE, spaceAfter=4 * mm),
        Table(
            [[
                Paragraph(f'<b>{v.ticker}</b>', s["ticker_big"]),
                Paragraph(
                    f'{v.fundamentals.company_name}<br/>'
                    f'<font color="{MUTED.hexval()}">{v.fundamentals.sector or ""}'
                    f' · {v.fundamentals.industry or ""}</font>',
                    s["company_name"],
                ),
                Paragraph(
                    f'<font color="{MUTED.hexval()}">{ts}</font>',
                    s["date_right"],
                ),
            ]],
            colWidths=["18%", "60%", "22%"],
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                ("ROWPADDING", (0, 0), (-1, -1), 8),
                ("ROUNDEDCORNERS", [4]),
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
            ]),
        ),
        Spacer(1, 5 * mm),
    ]
    return elements


def _build_alpha_score_banner(v: TickerValidation) -> list:
    s = _styles()
    score = v.alpha_score.total
    grade = v.alpha_score.grade
    rec = v.recommendation

    # Score bar drawing
    bar_w = 160 * mm
    bar_h = 8 * mm
    filled_w = (score / 100) * bar_w

    score_color = NEON_GREEN if score >= 70 else ELECTRIC_BLUE if score >= 50 else RED
    rec_color = NEON_GREEN if rec == "BUY_ZONE" else AMBER if rec == "WATCH" else RED

    d = Drawing(bar_w, bar_h)
    d.add(Rect(0, 0, bar_w, bar_h, fillColor=BORDER, strokeColor=None))
    d.add(Rect(0, 0, filled_w, bar_h, fillColor=score_color, strokeColor=None))

    data = [[
        Paragraph(
            f'<font color="{score_color.hexval()}" size="28"><b>{score:.0f}</b></font>'
            f'<font color="{MUTED.hexval()}" size="12">/100</font>',
            s["score_big"],
        ),
        Paragraph(
            f'<font color="{score_color.hexval()}" size="22"><b>{grade}</b></font>'
            f'<br/><font color="{MUTED.hexval()}" size="9">ALPHA GRADE</font>',
            s["center"],
        ),
        Paragraph(
            f'<font color="{rec_color.hexval()}" size="14"><b>{rec.replace("_", " ")}</b></font>'
            f'<br/><font color="{MUTED.hexval()}" size="9">RECOMMENDATION</font>',
            s["center"],
        ),
        Paragraph(
            f'<font color="{WHITE.hexval()}" size="12"><b>{v.stage.stage.value}</b></font>'
            f'<br/><font color="{MUTED.hexval()}" size="9">{v.stage.stage_weeks}w in stage</font>',
            s["center"],
        ),
    ]]

    elements = [
        Table(
            data,
            colWidths=["30%", "20%", "25%", "25%"],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("LINEAFTER", (0, 0), (2, 0), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWPADDING", (0, 0), (-1, -1), 10),
            ]),
        ),
        Spacer(1, 3 * mm),
    ]
    return elements


def _build_stage_section(v: TickerValidation) -> list:
    s = _styles()
    stage = v.stage

    stage_color = (
        NEON_GREEN if stage.stage.value == "Stage 2"
        else RED if stage.stage.value == "Stage 4"
        else AMBER
    )

    ma_rows = [
        ["Indicator", "Value", "Status"],
        ["Price", f"${stage.price:.2f}", "—"],
        ["MA 50", f"${stage.ma50:.2f}",
         "✓" if stage.price > stage.ma50 else "✗"],
        ["MA 150", f"${stage.ma150:.2f}" if stage.ma150 else "—",
         "✓" if stage.price > stage.ma150 and stage.ma150 else "✗"],
        ["MA 200", f"${stage.ma200:.2f}" if stage.ma200 else "—",
         "✓" if stage.price > stage.ma200 and stage.ma200 else "✗"],
        ["vs MA200", f"{stage.price_vs_ma200_pct:+.1f}%", "—"],
        ["MA Alignment", "Yes" if stage.ma_alignment else "No",
         "✓" if stage.ma_alignment else "✗"],
    ]

    elements = [
        Paragraph(
            f'<font color="{ELECTRIC_BLUE.hexval()}">◈ STAGE ANALYSIS</font>',
            s["section_title"],
        ),
        Spacer(1, 2 * mm),
        Table(
            ma_rows,
            colWidths=["40%", "35%", "25%"],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BORDER),
                ("BACKGROUND", (0, 1), (-1, -1), CARD_BG),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), ELECTRIC_BLUE),
                ("TEXTCOLOR", (0, 1), (-1, -1), WHITE),
                ("TEXTCOLOR", (2, 1), (2, -1), NEON_GREEN),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [CARD_BG, OXFORD_GREY]),
                ("GRID", (0, 0), (-1, -1), 0.25, BORDER),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWPADDING", (0, 0), (-1, -1), 5),
            ]),
        ),
        Spacer(1, 2 * mm),
        Paragraph(
            f'<font color="{stage_color.hexval()}"><b>● {stage.stage.value}</b></font>'
            f'  <font color="{MUTED.hexval()}" size="8">Confidence: {stage.confidence * 100:.0f}%</font>',
            s["normal"],
        ),
    ]

    if stage.notes:
        for note in stage.notes[:4]:
            elements.append(Paragraph(note, s["note"]))

    elements.append(Spacer(1, 4 * mm))
    return elements


def _build_confluence_checklist(v: TickerValidation) -> list:
    s = _styles()

    rows = [["Confluence Factor", "Value", "Result"]]
    for item in v.confluence_checklist:
        status_color = NEON_GREEN if item.passed else RED
        status_text = "● PASS" if item.passed else "● FAIL"
        rows.append([
            item.name,
            item.value or "—",
            Paragraph(
                f'<font color="{status_color.hexval()}"><b>{status_text}</b></font>',
                s["center"],
            ),
        ])

    passed = sum(1 for i in v.confluence_checklist if i.passed)
    total = len(v.confluence_checklist)

    elements = [
        Paragraph(
            f'<font color="{ELECTRIC_BLUE.hexval()}">◈ CONFLUENCE CHECKLIST</font>'
            f'  <font color="{MUTED.hexval()}" size="9">{passed}/{total} factors confirmed</font>',
            s["section_title"],
        ),
        Spacer(1, 2 * mm),
        Table(
            rows,
            colWidths=["60%", "20%", "20%"],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BORDER),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), ELECTRIC_BLUE),
                ("TEXTCOLOR", (0, 1), (1, -1), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [CARD_BG, OXFORD_GREY]),
                ("GRID", (0, 0), (-1, -1), 0.25, BORDER),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWPADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]),
        ),
        Spacer(1, 4 * mm),
    ]
    return elements


def _build_gex_section(v: TickerValidation) -> list:
    s = _styles()
    gex = v.gex

    if not gex.available:
        return [
            Paragraph(
                f'<font color="{ELECTRIC_BLUE.hexval()}">◈ GEX SUMMARY</font>'
                f'  <font color="{AMBER.hexval()}" size="8">ThetaData unavailable</font>',
                s["section_title"],
            ),
            Spacer(1, 4 * mm),
        ]

    gex_color = NEON_GREEN if gex.gex_total >= 0 else RED
    gex_label = "POSITIVE (dealer support)" if gex.gex_total >= 0 else "NEGATIVE (dealer selling)"

    def fmt_gex(v: float) -> str:
        return f"${v / 1e9:.2f}B" if abs(v) >= 1e9 else f"${v / 1e6:.1f}M"

    rows = [
        ["GEX Metric", "Value"],
        ["Net GEX", fmt_gex(gex.gex_total)],
        ["Call GEX", fmt_gex(gex.gex_call)],
        ["Put GEX", fmt_gex(gex.gex_put)],
        ["GEX Flip Level", f"${gex.gex_flip_level:.2f}" if gex.gex_flip_level else "—"],
        ["Put/Call Ratio", f"{gex.put_call_ratio:.2f}" if gex.put_call_ratio else "—"],
        ["IV Rank", f"{gex.iv_rank:.0f}" if gex.iv_rank else "—"],
    ]

    dominant = ", ".join(f"${s:.0f}" for s in gex.dominant_strikes[:3]) if gex.dominant_strikes else "—"
    rows.append(["Gamma Walls", dominant])

    elements = [
        Paragraph(
            f'<font color="{ELECTRIC_BLUE.hexval()}">◈ GEX SUMMARY</font>'
            f'  <font color="{gex_color.hexval()}" size="8">● {gex_label}</font>',
            s["section_title"],
        ),
        Spacer(1, 2 * mm),
        Table(
            rows,
            colWidths=["50%", "50%"],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BORDER),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), ELECTRIC_BLUE),
                ("TEXTCOLOR", (0, 1), (-1, -1), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [CARD_BG, OXFORD_GREY]),
                ("GRID", (0, 0), (-1, -1), 0.25, BORDER),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWPADDING", (0, 0), (-1, -1), 5),
            ]),
        ),
        Spacer(1, 4 * mm),
    ]
    return elements


def _build_fundamentals_section(v: TickerValidation) -> list:
    s = _styles()
    f = v.fundamentals

    def pct(val):
        return f"{val * 100:.1f}%" if val is not None else "—"

    def fmt_cap(val):
        if val is None:
            return "—"
        if val >= 1e12:
            return f"${val / 1e12:.2f}T"
        if val >= 1e9:
            return f"${val / 1e9:.1f}B"
        return f"${val / 1e6:.0f}M"

    rows = [
        ["Fundamental", "Value"],
        ["Market Cap", fmt_cap(f.market_cap)],
        ["Revenue TTM", fmt_cap(f.revenue_ttm)],
        ["Revenue Growth (YoY)", pct(f.revenue_growth_yoy)],
        ["Revenue Growth (QoQ)", pct(f.revenue_growth_qoq)],
        ["Earnings Growth (YoY)", pct(f.earnings_growth_yoy)],
        ["Gross Margin", pct(f.gross_margin)],
        ["Net Margin", pct(f.net_margin)],
        ["P/E Ratio", f"{f.pe_ratio:.1f}x" if f.pe_ratio else "—"],
        ["P/S Ratio", f"{f.ps_ratio:.2f}x" if f.ps_ratio else "—"],
        ["Institutional Ownership", pct(f.institutional_ownership_pct / 100) if f.institutional_ownership_pct else "—"],
        ["Short Float %", pct(f.short_float_pct / 100) if f.short_float_pct else "—"],
    ]

    elements = [
        Paragraph(
            f'<font color="{ELECTRIC_BLUE.hexval()}">◈ FUNDAMENTAL ANALYSIS</font>',
            s["section_title"],
        ),
        Spacer(1, 2 * mm),
        Table(
            rows,
            colWidths=["55%", "45%"],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BORDER),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, 0), ELECTRIC_BLUE),
                ("TEXTCOLOR", (0, 1), (-1, -1), WHITE),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [CARD_BG, OXFORD_GREY]),
                ("GRID", (0, 0), (-1, -1), 0.25, BORDER),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWPADDING", (0, 0), (-1, -1), 5),
            ]),
        ),
        Spacer(1, 4 * mm),
    ]
    return elements


def _build_price_trend_chart(v: TickerValidation) -> list:
    """Embed a simple closing price sparkline using ReportLab graphics."""
    s = _styles()

    try:
        ticker = v.ticker
        df = yf.download(ticker, period="6mo", progress=False, auto_adjust=True)
        if df is None or df.empty:
            return []

        close = df["Close"].dropna().tolist()
        if len(close) < 10:
            return []

        # Downsample to ~60 points for clean rendering
        step = max(1, len(close) // 60)
        prices = close[::step][-60:]
        n = len(prices)

        chart_w = 160 * mm
        chart_h = 35 * mm
        pad_l, pad_r, pad_t, pad_b = 8, 5, 5, 8

        d = Drawing(chart_w, chart_h)

        # Background
        d.add(Rect(0, 0, chart_w, chart_h, fillColor=CARD_BG, strokeColor=BORDER, strokeWidth=0.5))

        # Grid lines
        p_min, p_max = min(prices), max(prices)
        p_range = p_max - p_min or 1
        for i in range(3):
            y = pad_b + (i + 1) * (chart_h - pad_t - pad_b) / 4
            d.add(Line(pad_l, y, chart_w - pad_r, y, strokeColor=BORDER, strokeWidth=0.3))

        # Price line (gradient color: neon green if trending up)
        def px(i):
            return pad_l + i * (chart_w - pad_l - pad_r) / (n - 1)

        def py(price):
            return pad_b + (price - p_min) / p_range * (chart_h - pad_t - pad_b)

        # Build polyline points
        points = []
        for i, price in enumerate(prices):
            points.extend([px(i), py(price)])

        trend_up = prices[-1] > prices[0]
        line_color = NEON_GREEN if trend_up else RED

        d.add(PolyLine(points, strokeColor=line_color, strokeWidth=1.5, fillColor=None))

        # Current price label
        last_price = prices[-1]
        d.add(String(
            chart_w - pad_r - 2,
            py(last_price),
            f"${last_price:.2f}",
            fontName="Helvetica-Bold",
            fontSize=7,
            fillColor=line_color,
            textAnchor="end",
        ))

        # X-axis label
        d.add(String(
            pad_l, 1,
            "6 Month Price History",
            fontName="Helvetica",
            fontSize=6,
            fillColor=MUTED,
        ))

        elements = [
            Paragraph(
                f'<font color="{ELECTRIC_BLUE.hexval()}">◈ PRICE TREND</font>',
                s["section_title"],
            ),
            Spacer(1, 2 * mm),
            d,
            Spacer(1, 4 * mm),
        ]
        return elements

    except Exception:
        return []


def _build_footer(v: TickerValidation) -> list:
    s = _styles()
    return [
        HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=2 * mm),
        Paragraph(
            f'<font color="{MUTED.hexval()}" size="7">'
            f"Alpha Station v4.0 · This report is for informational purposes only and does not constitute investment advice. "
            f"Generated: {v.timestamp} · Ticker: {v.ticker}"
            f"</font>",
            s["footer"],
        ),
    ]


# ── Style registry ─────────────────────────────────────────────────────────────

def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "brand": ParagraphStyle(
            "brand",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=MUTED,
            spaceAfter=2,
        ),
        "report_subtitle": ParagraphStyle(
            "report_subtitle",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=WHITE,
            spaceAfter=4,
        ),
        "ticker_big": ParagraphStyle(
            "ticker_big",
            fontName="Helvetica-Bold",
            fontSize=26,
            textColor=NEON_GREEN,
            leading=28,
        ),
        "company_name": ParagraphStyle(
            "company_name",
            fontName="Helvetica",
            fontSize=11,
            textColor=WHITE,
            leading=16,
        ),
        "date_right": ParagraphStyle(
            "date_right",
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            alignment=TA_RIGHT,
        ),
        "score_big": ParagraphStyle(
            "score_big",
            fontName="Helvetica-Bold",
            fontSize=28,
            textColor=WHITE,
            alignment=TA_CENTER,
            leading=32,
        ),
        "center": ParagraphStyle(
            "center",
            fontName="Helvetica",
            fontSize=9,
            textColor=WHITE,
            alignment=TA_CENTER,
            leading=14,
        ),
        "section_title": ParagraphStyle(
            "section_title",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=ELECTRIC_BLUE,
            spaceBefore=6,
            spaceAfter=2,
        ),
        "normal": ParagraphStyle(
            "normal",
            fontName="Helvetica",
            fontSize=9,
            textColor=WHITE,
        ),
        "note": ParagraphStyle(
            "note",
            fontName="Helvetica",
            fontSize=8,
            textColor=MUTED,
            leftIndent=8,
        ),
        "footer": ParagraphStyle(
            "footer",
            fontName="Helvetica",
            fontSize=7,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
    }
