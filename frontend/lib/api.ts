/**
 * Alpha Station v4.0 — API Client
 */

const BASE = "/api/v1";

export interface StageResult {
  stage: string;
  confidence: number;
  ma50: number;
  ma150: number;
  ma200: number;
  price: number;
  price_vs_ma200_pct: number;
  ma_alignment: boolean;
  price_above_all_mas: boolean;
  transitioning_to_2: boolean;
  stage_weeks: number;
  notes: string[];
}

export interface GEXResult {
  ticker: string;
  gex_total: number;
  gex_call: number;
  gex_put: number;
  gex_flip_level: number | null;
  dominant_strikes: number[];
  iv_rank: number | null;
  put_call_ratio: number | null;
  available: boolean;
  error?: string;
}

export interface LiquidityResult {
  ticker: string;
  rvol: number;
  avg_volume_20d: number;
  current_volume: number;
  vwap: number | null;
  vwap_anchored: number | null;
  stage2_alert: boolean;
}

export interface FundamentalResult {
  ticker: string;
  company_name: string;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  revenue_growth_yoy: number | null;
  revenue_growth_qoq: number | null;
  earnings_growth_yoy: number | null;
  gross_margin: number | null;
  net_margin: number | null;
  revenue_ttm: number | null;
  pe_ratio: number | null;
  ps_ratio: number | null;
  institutional_ownership_pct: number | null;
  short_float_pct: number | null;
  float_shares: number | null;
  revenue_accelerating: boolean;
  earnings_positive: boolean;
  low_institutional_coverage: boolean;
  high_growth: boolean;
}

export interface ConfluenceItem {
  name: string;
  passed: boolean;
  value: string | null;
  weight: number;
}

export interface AlphaScore {
  total: number;
  stage_score: number;
  rvol_score: number;
  fundamental_score: number;
  technical_score: number;
  grade: string;
}

export interface TickerValidation {
  ticker: string;
  timestamp: string;
  stage: StageResult;
  liquidity: LiquidityResult;
  fundamentals: FundamentalResult;
  confluence_checklist: ConfluenceItem[];
  alpha_score: AlphaScore;
  recommendation: string;
  key_levels: Record<string, number>;
}

export interface BubbleDataPoint {
  ticker: string;
  company_name: string;
  revenue_growth: number;
  market_cap_billions: number;
  rvol: number;
  stage: string;
  alpha_score: number;
  sector: string | null;
  stage2_alert: boolean;
}

export interface AlertEvent {
  ticker: string;
  alert_type: string;
  message: string;
  severity: "HIGH" | "MEDIUM" | "LOW";
  timestamp: string;
  data: Record<string, unknown>;
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

  alerts: (tickers?: string) =>
    apiFetch<AlertEvent[]>(
      `${BASE}/alerts${tickers ? `?tickers=${encodeURIComponent(tickers)}` : ""}`
    ),

  hiddenGems: (tickers?: string) =>
    apiFetch<TickerValidation[]>(
      `${BASE}/screener/hidden-gems${tickers ? `?tickers=${encodeURIComponent(tickers)}` : ""}`
    ),

  reportUrl: (ticker: string) => `${BASE}/report/${ticker}`,
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

export function fmtGex(val: number): string {
  if (Math.abs(val) >= 1e9) return `${(val / 1e9).toFixed(2)}B`;
  if (Math.abs(val) >= 1e6) return `${(val / 1e6).toFixed(1)}M`;
  return val.toFixed(0);
}

export function stageColor(stage: string): string {
  switch (stage) {
    case "Stage 2": return "#00FF87";
    case "Stage 1": return "#FFB800";
    case "Stage 3": return "#FF9800";
    case "Stage 4": return "#FF4560";
    default: return "#6B7A99";
  }
}

export function recColor(rec: string): string {
  if (rec === "BUY_ZONE") return "#00FF87";
  if (rec === "WATCH") return "#FFB800";
  return "#FF4560";
}
