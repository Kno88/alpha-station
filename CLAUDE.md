# Alpha Station — AI Assistant Guide

## Project Overview

Alpha Station v6.0 is an **institutional-grade quantitative stock screening terminal** that evaluates US equities using fundamental analysis. It assigns an Alpha Score (0–100) based on growth, profitability, moat, and financial health metrics sourced from yfinance.

**Monorepo structure:**
```
alpha-station/
├── backend/          # Python 3.11 + FastAPI
│   ├── main.py       # App entry point & all API routes
│   ├── config.py     # Pydantic-settings configuration
│   ├── models.py     # Pydantic v2 data models
│   └── modules/
│       ├── fundamentals.py   # FundamentalsEngine (yfinance data fetching)
│       ├── alpha_scorer.py   # AlphaScore computation (0-100)
│       ├── pdf_generator.py  # ReportLab PDF generation
│       ├── stage_analysis.py # LEGACY — not used by main.py
│       ├── rs_engine.py      # LEGACY — not used by main.py
│       ├── liquidity_engine.py # LEGACY — not used by main.py
│       └── risk_manager.py   # LEGACY — not used by main.py
└── frontend/         # Next.js 16 + TypeScript + Tailwind
    ├── app/          # App Router pages
    ├── components/   # React components
    └── lib/api.ts    # Typed API client
```

---

## Backend

### Running locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Swagger UI: `http://localhost:8000/docs`  
Health check: `http://localhost:8000/health`

### API routes (`/api/v1/`)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/validate/{ticker}` | Full fundamental analysis + Alpha Score |
| GET | `/report/{ticker}` | Download PDF report |
| GET | `/bubble-data?tickers=...` | Data for Alpha Bubble Chart |
| GET | `/screener/hidden-gems?tickers=...` | Screen small/mid-caps, sorted by Alpha Score |
| POST | `/screener/advanced?tickers=...` | Advanced screener with `ScreenerFilters` body |
| GET | `/market-tape` | Live prices for SPY, QQQ, DIA, IWM, AAPL, MSFT, NVDA, BTC |

All screener endpoints cap tickers at 12 (hidden-gems) or 25 (advanced). Concurrent yfinance fetches are throttled with `asyncio.Semaphore(4)` and a 30-second per-ticker timeout.

### Configuration (`config.py`)

Settings class uses `pydantic_settings.BaseSettings` with env prefix `ALPHA_`. Key environment variables:

| Var | Default | Purpose |
|-----|---------|---------|
| `ALPHA_FMP_API_KEY` | `demo` | Financial Modeling Prep (optional, currently unused) |
| `ALPHA_POLYGON_API_KEY` | `""` | Polygon.io (optional, currently unused) |
| `ALPHA_CORS_ORIGINS` | `http://localhost:3000,...` | Comma-separated allowed origins |
| `PDF_OUTPUT_DIR` | `./alpha_reports` | PDF storage directory |
| `DEBUG` | `False` | Debug mode |

The `cors_origins` field is a **comma-separated string** (not a JSON list) to avoid Pydantic parsing issues. It is split via the `cors_origins_list` property.

### Data models (`models.py`)

All `FundamentalResult` numeric fields use `Optional[float]` and return `None` when data is unavailable. Ratio conventions:

- **Growth/margin fields** are decimals: `revenue_growth_yoy=0.25` means 25%
- **`institutional_ownership_pct`** and **`short_float_pct`** are stored as full percentages: `28.0` means 28%
- **`market_cap`** and currency fields are in raw USD (not billions)

Key models: `FundamentalResult`, `AlphaScore`, `TickerValidation`, `ScreenerFilters`, `BubbleDataPoint`, `MarketTapeItem`.

### Alpha Score engine (`modules/alpha_scorer.py`)

Score breakdown (max 100 pts):

| Component | Max | Key signals |
|-----------|-----|-------------|
| Growth | 30 | Rev growth ≥20%, Rule of 40, Operating leverage >1x, Earnings growth |
| Profitability | 30 | Net margin, Gross margin expansion, ROE |
| Moat | 20 | Wide/Narrow moat heuristic, R&D intensity ≥10%, Rev/employee ≥$500K |
| Health | 20 | Net cash position, Piotroski F-Score ≥7, Low analyst coverage |

Grade mapping: A+ ≥90, A ≥80, B+ ≥70, B ≥60, C ≥50, D ≥40, F <40  
Recommendation: STRONG_BUY ≥75, BUY ≥60, HOLD ≥40, AVOID <40

### Fundamentals engine (`modules/fundamentals.py`)

`FundamentalsEngine.fetch(ticker)` is the single entry point. All data comes from `yfinance.Ticker`. When primary `info` fields are missing, the engine falls back to `balance_sheet`, `income_stmt`, and `cash_flow` DataFrames. Moat is a heuristic based on margin thresholds; there is no external moat API.

Key computed metrics (not from yfinance directly):
- `rule_of_40` — Rev Growth% + FCF Margin%
- `operating_leverage` — Operating income growth / revenue growth
- `gross_margin_expansion` — GM current year minus GM prior year
- `piotroski_f_score` — 9-point quality score (simplified implementation; point 7 "dilution" is skipped)
- `altman_z_score` — Bankruptcy predictor
- `revenue_cagr_3y` — 3-year compound annual growth rate

### Running tests

```bash
cd backend
pytest tests/ -v
```

> **Known issue:** `tests/test_alpha_scorer.py` was written for an older version of the scorer that accepted `StageResult`, `LiquidityResult`, and `RSLineResult` arguments. The current v6.0 scorer only accepts `FundamentalResult`. These tests will fail until updated.

---

## Frontend

### Running locally

```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
```

```bash
npm run build        # Production build
npm run lint         # ESLint check
```

### Pages

| Route | File | Description |
|-------|------|-------------|
| `/` | `app/page.tsx` | Main dashboard: TickerValidator + AlphaBubbleChart + HiddenGemsTable |
| `/screener` | `app/screener/page.tsx` | AdvancedScreener with filter UI |
| `/validator` | `app/validator/page.tsx` | Standalone ticker validation view |

### Components

- `TickerValidator` — Search input, fetches `/validate/{ticker}`, displays radar chart + confluence checklist + PDF download
- `AlphaBubbleChart` — Scatter/bubble chart (Chart.js): Revenue Growth% × Market Cap, bubble size = Alpha Score
- `HiddenGemsTable` — AG Grid table fetching `/screener/hidden-gems`
- `AdvancedScreener` — Full screener UI with collapsible filter panels, posts to `/screener/advanced`
- `NomenclaturePanel` — Reference panel explaining scoring methodology
- `ui/Navbar` — Top navigation bar
- `ui/TickerTape` — Scrolling live market tape (fetches `/market-tape`)
- `ui/StatBar` — Inline stats display

### API client (`lib/api.ts`)

**Production URL is hardcoded** to `https://alpha-station.onrender.com/api/v1`. For local development, update the `BASE` constant or use an environment variable.

Exported utilities:
- `api.validate(ticker)` — GET validate
- `api.bubbleData(tickers?)` — GET bubble-data
- `api.hiddenGems(tickers?)` — GET hidden-gems
- `api.advancedScreener(tickers, filters)` — POST advanced screener
- `api.reportUrl(ticker)` — returns the PDF download URL string
- `api.marketTape()` — GET market-tape
- `fmtPct(val, multiply?)` — Format decimal to `+25.0%` string
- `fmtCap(val)` — Format USD to `$1.2B` / `$500M` string
- `recColor(rec)` — Map recommendation string to hex color

### Styling conventions

The project uses a **dark institutional terminal aesthetic**. Custom Tailwind utility classes defined in `globals.css`:

| Class | Purpose |
|-------|---------|
| `.glass` | Frosted glass card with backdrop-blur, subtle border |
| `.glass-panel` | Lighter version, used inside headers |
| `.card` | Standard dark card with hover border brightening |
| `.card-header` | Electric-blue left-border label, monospace, uppercase |
| `.btn-primary` | Blue gradient button with shimmer animation |

Custom Tailwind colors: `background` (#050505), `electric-blue` (#3B82F6), `neon-green` (#10B981), `amber` (#F59E0B), `danger` (#EF4444), `muted` (#737373).

Fonts: **JetBrains Mono** for all monospace/terminal text, **Inter** for body.

AG Grid uses `.ag-theme-alpine-dark` with custom CSS variables to match the dark theme.

---

## Deployment

### Backend — Railway

- Config: `backend/railway.toml`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Health check: `/health`
- Docker: `backend/Dockerfile` (Python 3.11-slim)
- Live URL: `https://alpha-station.onrender.com` (note: Render, not Railway — the Render URL is hardcoded in `lib/api.ts`)

### Frontend — Vercel

- Config: `frontend/vercel.json`
- Framework: Next.js (auto-detected)
- Build: `npm run build`
- The `.env.example` shows `BACKEND_URL` but this is not currently read by the app (URL is hardcoded in `lib/api.ts`)

### Windows local dev

`start.bat` installs deps and launches both services in separate terminal windows:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

---

## Key conventions for AI agents

1. **Never add comments explaining what code does** — only add comments for non-obvious WHY (invariants, workarounds, hidden constraints).

2. **Financial metric units are inconsistent by design** — ownership/short percentages are stored as `28.0` (percent), while growth/margin ratios are decimals `0.28`. Do not "normalize" these without updating all consumers.

3. **Legacy modules exist but are unused** — `stage_analysis.py`, `rs_engine.py`, `liquidity_engine.py`, `risk_manager.py` are NOT imported by `main.py`. They were part of v4/v5 and retain technical indicator logic (Weinstein stages, RS lines, VCP patterns). Do not delete without confirming they are not needed for a future version.

4. **Tests reference the old API** — `tests/test_alpha_scorer.py` imports `StageResult`, `LiquidityResult`, `RSLineResult` which no longer exist in `models.py`. These tests need to be rewritten for the v6.0 fundamental-only scorer before they can pass.

5. **Screener concurrency limit** — All multi-ticker endpoints use `asyncio.Semaphore(4)` to avoid overwhelming yfinance. Do not remove or raise this without testing rate limit behavior.

6. **Alpha Score weights in config are not used** — `config.py` defines `weight_stage`, `weight_rs_line`, `weight_fundamental`, `weight_rvol` as a holdover from v5.0. The current `alpha_scorer.py` uses hardcoded point values, not these weights.

7. **Frontend type definitions mirror backend Pydantic models** — When adding a new field to `models.py`, add the matching TypeScript interface in `lib/api.ts`. Both must stay in sync.

8. **CORS origins must be a comma-separated string** in the env var, not a JSON array: `ALPHA_CORS_ORIGINS=http://localhost:3000,https://myapp.vercel.app`.
