"""
Alpha Station v6.0 — PDF Report Generator
Fundamental Analysis Only
"""

from __future__ import annotations

import io
import os
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Optional

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
from reportlab.graphics import renderPDF

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
    story += _build_radar_section(validation)
    story += _build_confluence_checklist(validation)
    story += _build_fundamentals_section(validation)
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
            f'<font color="{ELECTRIC_BLUE.hexval()}">■</font> ALPHA STATION v6.0',
            s["brand"],
        ),
        Paragraph(
            f'<font color="{WHITE.hexval()}">FUNDAMENTAL INTELLIGENCE REPORT</font>',
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
    rec_color = NEON_GREEN if rec in ["STRONG_BUY", "BUY"] else AMBER if rec == "HOLD" else RED

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
    ]]

    elements = [
        Table(
            data,
            colWidths=["34%", "33%", "33%"],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                ("BOX", (0, 0), (-1, -1), 1, BORDER),
                ("LINEAFTER", (0, 0), (1, 0), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWPADDING", (0, 0), (-1, -1), 10),
            ]),
        ),
        Spacer(1, 3 * mm),
    ]
    return elements


def _build_radar_section(v: TickerValidation) -> list:
    s = _styles()
    
    # Data for fundamental radar
    labels = np.array(['Growth', 'Profitability', 'Moat', 'Health'])
    
    # Map scores appropriately
    # growth is /30, profit is /30, moat is /20, health is /20
    # normalize each to 100 for the radar
    stats = np.array([
        (v.alpha_score.growth_score / 30.0) * 100,
        (v.alpha_score.profitability_score / 30.0) * 100,
        (v.alpha_score.moat_score / 20.0) * 100,
        (v.alpha_score.health_score / 20.0) * 100
    ])
    
    angles = np.linspace(0, 2*np.pi, len(labels), endpoint=False)
    stats = np.concatenate((stats, [stats[0]]))
    angles = np.concatenate((angles, [angles[0]]))
    
    # Plotting
    fig, ax = plt.subplots(figsize=(3, 3), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor('#1C2333')
    ax.set_facecolor('#242E42')
    
    ax.plot(angles, stats, 'o-', linewidth=2, color='#00FF87')
    ax.fill(angles, stats, alpha=0.25, color='#00FF87')
    
    ax.set_thetagrids(angles[:-1] * 180/np.pi, labels, color='#E8EBF0', fontsize=10, fontweight='bold')
    
    ax.set_rticks([20, 40, 60, 80, 100])
    ax.set_yticklabels([])
    ax.grid(color='#2D3A52', linestyle='--')
    ax.spines['polar'].set_color('#2D3A52')
    
    plt.tight_layout()
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    
    img = Image(buf, width=2.5 * inch, height=2.5 * inch)
    
    table_data = [[
        Paragraph(
            f'<font color="{ELECTRIC_BLUE.hexval()}">◈ FUNDAMENTAL PROFILE</font>',
            s["section_title"],
        ), ""
    ], [
        Table(
            [
                ["Metric", "Score"],
                ["Growth", f"{v.alpha_score.growth_score:.1f}/30"],
                ["Profitability", f"{v.alpha_score.profitability_score:.1f}/30"],
                ["Moat", f"{v.alpha_score.moat_score:.1f}/20"],
                ["Health", f"{v.alpha_score.health_score:.1f}/20"],
                ["Quality Rank", f"{v.alpha_score.quality_rank}/100"],
                ["Value Rank", f"{v.alpha_score.value_rank}/100"]
            ],
            colWidths=[1.5*inch, 1*inch],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), BORDER),
                ("TEXTCOLOR", (0, 0), (-1, 0), ELECTRIC_BLUE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 1), (-1, -1), WHITE),
                ("GRID", (0, 0), (-1, -1), 0.25, BORDER),
                ("ROWPADDING", (0, 0), (-1, -1), 6),
            ])
        ),
        img
    ]]
    
    return [
        Table(
            table_data,
            colWidths=["50%", "50%"],
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (1, 1), "CENTER"),
            ])
        ),
        Spacer(1, 4 * mm)
    ]


def _build_confluence_checklist(v: TickerValidation) -> list:
    s = _styles()

    rows = [["Fundamental Factor", "Value", "Result"]]
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
            f'<font color="{ELECTRIC_BLUE.hexval()}">◈ FUNDAMENTAL CHECKLIST</font>'
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
        ["Earnings Growth (YoY)", pct(f.earnings_growth_yoy)],
        ["P/E Ratio", f"{f.pe_ratio:.1f}x" if f.pe_ratio else "—"],
        ["FCF Yield", pct(f.fcf_yield)],
        ["Earnings Yield", pct(f.earnings_yield)],
        ["Piotroski F-Score", f"{f.piotroski_f_score:.0f}/9" if f.piotroski_f_score is not None else "—"],
        ["Altman Z-Score", f"{f.altman_z_score:.2f}" if f.altman_z_score is not None else "—"],
        ["Debt to FCF", f"{f.debt_to_fcf:.2f}x" if f.debt_to_fcf is not None else "—"],
        ["Capex to Revenue", pct(f.capex_to_revenue)],
        ["Institutional Ownership", pct(f.institutional_ownership_pct / 100) if f.institutional_ownership_pct else "—"],
        ["Market Share", f"{f.market_share_pct:.1f}%" if f.market_share_pct is not None else "—"],
        ["Economic Moat", f"{f.moat}" if f.moat else "—"],
    ]

    elements = [
        Paragraph(
            f'<font color="{ELECTRIC_BLUE.hexval()}">◈ INSTITUTIONAL FUNDAMENTALS</font>',
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


def _build_footer(v: TickerValidation) -> list:
    s = _styles()
    return [
        HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=2 * mm),
        Paragraph(
            f'<font color="{MUTED.hexval()}" size="7">'
            f"Alpha Station v6.0 · This report is for informational purposes only and does not constitute investment advice. "
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
