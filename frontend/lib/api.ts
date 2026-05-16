/**
 * Alpha Station v6.0 — Fundamental API Client
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "";
const BASE = BACKEND_URL ? `${BACKEND_URL}/api/v1` : "/api/v1";

export interface FundamentalResult {
  ticker: string;
  company_name: string;
  sector: string | null;
  industry: string | null;
  // Valuación
  market_cap: number | null;
  pe_ratio: number | null;
  ps_ratio: number | null;
  peg_ratio: number | null;
  ev_to_ebitda: number | null;
  price_to_book: number | null;
  forward_pe: number | null;
  fcf_yield: number | null;
  earnings_yield: number | null;
  // Crecimiento
  revenue_ttm: number | null;
  revenue_growth_yoy: number | null;
  revenue_growth_qoq: number | null;
  revenue_cagr_3y: number | null;
  earnings_growth_yoy: number | null;
  earnings_growth_qoq: number | null;
  fcf_growth: number | null;
  capex_to_revenue: number | null;
  // Rentabilidad
  gross_margin: number | null;
  operating_margin: number | null;
  net_margin: number | null;
  fcf_margin: number | null;
  roe: number | null;
  roa: number | null;
  roic: number | null;
  // Balance Sheet
  total_debt: number | null;
  total_equity: number | null;
  total_assets: number | null;
  cash_and_equiv: number | null;
  debt_to_equity: number | null;
  debt_to_ebitda: number | null;
  current_ratio: number | null;
  quick_ratio: number | null;
  interest_coverage: number | null;
  net_debt: number | null;
  debt_to_fcf: number | null;
  // Liquidez
  avg_volume_20d: number | null;
  current_volume: number | null;
  float_shares: number | null;
  short_float_pct: number | null;
  // Institucional
  institutional_ownership_pct: number | null;
  insider_ownership_pct: number | null;
  // Calidad
  piotroski_f_score: number | null;
  altman_z_score: number | null;
  earnings_surprise_pct: number | null;
  accruals_ratio: number | null;
  fcf_to_net_income: number | null;
  // V6 Moat & Market Share
  moat: string | null;
  market_share_pct: number | null;
  // Price history for sparklines
  price_history_20d: number[] | null;
  // Booleans
  revenue_accelerating: boolean;
  earnings_positive: boolean;
  low_institutional_coverage: boolean;
  high_growth: boolean;
  profitable: boolean;
  positive_fcf: boolean;
  low_debt: boolean;
}

export interface ConfluenceItem {
  name: string;
  passed: boolean;
  value: string | null;
  weight: number;
}

export interface AlphaScore {
  total: number;
  growth_score: number;
  profitability_score: number;
  moat_score: number;
  health_score: number;
  quality_rank: number;
  value_rank: number;
  grade: string;
}

export interface TickerValidation {
  ticker: string;
  timestamp: string;
  fundamentals: FundamentalResult;
  confluence_checklist: ConfluenceItem[];
  alpha_score: AlphaScore;
  recommendation: string;
}

export interface BubbleDataPoint {
  ticker: string;
  company_name: string;
  revenue_growth: number;
  market_cap_billions: number;
  alpha_score: number;
  sector: string | null;
  moat: string | null;
}

export interface ScreenerFilters {
  // Valuación
  pe_min?: number | null;
  pe_max?: number | null;
  ps_min?: number | null;
  ps_max?: number | null;
  peg_min?: number | null;
  peg_max?: number | null;
  ev_ebitda_min?: number | null;
  ev_ebitda_max?: number | null;
  // Crecimiento
  revenue_growth_min?: number | null;
  earnings_growth_min?: number | null;
  revenue_cagr_3y_min?: number | null;
  fcf_growth_min?: number | null;
  // Rentabilidad
  gross_margin_min?: number | null;
  operating_margin_min?: number | null;
  net_margin_min?: number | null;
  roe_min?: number | null;
  roa_min?: number | null;
  roic_min?: number | null;
  // Balance Sheet
  debt_to_equity_max?: number | null;
  debt_to_ebitda_max?: number | null;
  current_ratio_min?: number | null;
  quick_ratio_min?: number | null;
  interest_coverage_min?: number | null;
  // Liquidez & Tamaño
  market_cap_min?: number | null;
  market_cap_max?: number | null;
  avg_volume_min?: number | null;
  short_interest_max?: number | null;
  // Calidad
  piotroski_f_score_min?: number | null;
  altman_z_score_min?: number | null;
  accruals_ratio_max?: number | null;
  fcf_yield_min?: number | null;
  debt_to_fcf_max?: number | null;
  institutional_ownership_min?: number | null;
  institutional_ownership_max?: number | null;
  // General
  alpha_score_min?: number | null;
  sectors?: string[] | null;
}

export interface MarketTapeItem {
  symbol: string;
  price: number;
  change: number;
  percent: number;
}

// ── Fetch helpers ──────────────────────────────────────────────────────────────

async function apiFetch<T>(path: string, timeoutMs = 60_000): Promise<T> {
  const controller = new AbortController();
  const tid = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(path, { cache: "no-store", signal: controller.signal });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? `API error ${res.status}`);
    }
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(tid);
  }
}

export const api = {
  validate: (ticker: string) =>
    apiFetch<TickerValidation>(`${BASE}/validate/${ticker}`),

  bubbleData: (tickers?: string) =>
    apiFetch<BubbleDataPoint[]>(
      `${BASE}/bubble-data${tickers ? `?tickers=${encodeURIComponent(tickers)}` : ""}`
    ),

  hiddenGems: (tickers?: string) =>
    apiFetch<TickerValidation[]>(
      `${BASE}/screener/hidden-gems${tickers ? `?tickers=${encodeURIComponent(tickers)}` : ""}`
    ),

  advancedScreener: async (
    tickers: string,
    filters: ScreenerFilters
  ): Promise<TickerValidation[]> => {
    const path = `${BASE}/screener/advanced?tickers=${encodeURIComponent(tickers)}`;
    const controller = new AbortController();
    const tid = setTimeout(() => controller.abort(), 60_000);
    try {
      const res = await fetch(path, {
        method: "POST",
        cache: "no-store",
        signal: controller.signal,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(filters),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail ?? `API error ${res.status}`);
      }
      return res.json() as Promise<TickerValidation[]>;
    } finally {
      clearTimeout(tid);
    }
  },

  reportUrl: (ticker: string) => `${BASE}/report/${ticker}`,

  marketTape: () => apiFetch<MarketTapeItem[]>(`${BASE}/market-tape`),
};

// ── Formatting utils ───────────────────────────────────────────────────────────

export function fmtPct(val: number | null | undefined, multiply = false): string {
  if (val == null) return "—";
  const v = multiply ? val * 100 : val;
  return `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`;
}

export function fmtCap(val: number | null | undefined): string {
  if (val == null) return "—";
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9) return `$${(val / 1e9).toFixed(1)}B`;
  if (val >= 1e6) return `$${(val / 1e6).toFixed(0)}M`;
  return `$${val.toLocaleString()}`;
}

export function recColor(rec: string): string {
  if (rec === "STRONG_BUY" || rec === "BUY") return "#00FF87";
  if (rec === "HOLD") return "#FFB800";
  return "#FF4560";
}
