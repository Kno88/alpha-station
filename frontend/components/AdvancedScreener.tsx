"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AgGridReact } from "ag-grid-react";
import type {
  ColDef,
  ICellRendererParams,
  ValueFormatterParams,
  RowClassParams,
} from "ag-grid-community";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import {
  api,
  TickerValidation,
  ScreenerFilters,
  fmtCap,
  fmtPct,
  recColor,
} from "@/lib/api";
import { toast } from "react-toastify";
import {
  RefreshCw,
  Loader2,
  ChevronDown,
  ChevronUp,
  RotateCcw,
} from "lucide-react";
import clsx from "clsx";

// ── Default filter values ──────────────────────────────────────────────────
const DEFAULT_FILTERS: ScreenerFilters = {
  pe_max: 30,
  ps_max: 3,
  peg_max: 1.5,
  ev_ebitda_max: 15,
  revenue_growth_min: 0.15,
  earnings_growth_min: 0.2,
  gross_margin_min: 0.3,
  operating_margin_min: 0.1,
  net_margin_min: 0.05,
  roe_min: 0.15,
  roa_min: 0.08,
  debt_to_equity_max: 1.5,
  debt_to_fcf_max: 3.0,
  current_ratio_min: 1.5,
  market_cap_min: 50e6,
  market_cap_max: 5e9,
  short_interest_max: 0.2,
  piotroski_f_score_min: 6,
  altman_z_score_min: 3.0,
  fcf_yield_min: 0.03,
  institutional_ownership_min: 0.1,
  institutional_ownership_max: 0.5,
  alpha_score_min: 50,
};

const GURU_SCREENS: Record<string, Partial<ScreenerFilters>> = {
  "Minervini Trend": {
    pe_max: null, ps_max: null, peg_max: null, ev_ebitda_max: null,
    revenue_growth_min: 0.20, earnings_growth_min: 0.20,
    gross_margin_min: null, operating_margin_min: null, net_margin_min: null,
    roe_min: null, roa_min: null, debt_to_equity_max: null, debt_to_fcf_max: null,
    current_ratio_min: null, market_cap_min: 300e6, market_cap_max: null,
    short_interest_max: null, piotroski_f_score_min: null, altman_z_score_min: null,
    fcf_yield_min: null, institutional_ownership_min: 0.1, institutional_ownership_max: null,
    alpha_score_min: 70,
  },
  "Piotroski Quality": {
    pe_max: 20, ps_max: null, peg_max: null, ev_ebitda_max: null,
    revenue_growth_min: null, earnings_growth_min: null,
    gross_margin_min: 0.2, operating_margin_min: null, net_margin_min: null,
    roe_min: 0.15, roa_min: null, debt_to_equity_max: 1.0, debt_to_fcf_max: 3.0,
    current_ratio_min: 1.5, market_cap_min: 100e6, market_cap_max: null,
    short_interest_max: null, piotroski_f_score_min: 8, altman_z_score_min: 3.0,
    fcf_yield_min: 0.05, institutional_ownership_min: null, institutional_ownership_max: null,
    alpha_score_min: 50,
  },
  "CAN SLIM Growth": {
    pe_max: 50, ps_max: 10, peg_max: null, ev_ebitda_max: null,
    revenue_growth_min: 0.25, earnings_growth_min: 0.25,
    gross_margin_min: null, operating_margin_min: null, net_margin_min: null,
    roe_min: 0.17, roa_min: null, debt_to_equity_max: 1.5, debt_to_fcf_max: null,
    current_ratio_min: null, market_cap_min: 500e6, market_cap_max: null,
    short_interest_max: null, piotroski_f_score_min: null, altman_z_score_min: null,
    fcf_yield_min: null, institutional_ownership_min: 0.2, institutional_ownership_max: null,
    alpha_score_min: 60,
  },
  "Deep Value FCF": {
    pe_max: 15, ps_max: 1.5, peg_max: 1.0, ev_ebitda_max: 10,
    revenue_growth_min: null, earnings_growth_min: null,
    gross_margin_min: null, operating_margin_min: null, net_margin_min: null,
    roe_min: null, roa_min: null, debt_to_equity_max: 1.0, debt_to_fcf_max: 2.0,
    current_ratio_min: 1.5, market_cap_min: 50e6, market_cap_max: null,
    short_interest_max: null, piotroski_f_score_min: 6, altman_z_score_min: 3.0,
    fcf_yield_min: 0.08, institutional_ownership_min: null, institutional_ownership_max: null,
    alpha_score_min: 40,
  }
};

// ── Cell renderers ────────────────────────────────────────────────────────
function MoatCellRenderer({ value }: ICellRendererParams) {
  const moat = value as string;
  const color = moat === "Wide" ? "#00FF87" : moat === "Narrow" ? "#0088FF" : "#6B7A99";
  return (
    <span
      className="inline-block px-2 py-0.5 rounded text-xs font-mono font-semibold"
      style={{
        color,
        background: color + "15",
        border: `1px solid ${color}30`,
      }}
    >
      {moat || "None"}
    </span>
  );
}

function RecCellRenderer({ value }: ICellRendererParams) {
  const color = recColor(value as string);
  return (
    <span
      className="inline-block px-2.5 py-0.5 rounded-full text-xs font-mono font-bold"
      style={{
        color,
        background: color + "15",
        border: `1px solid ${color}30`,
      }}
    >
      {(value as string).replace("_", " ")}
    </span>
  );
}

function ScoreCellRenderer({ value }: ICellRendererParams) {
  const score = value as number;
  const color = score >= 70 ? "#00FF87" : score >= 50 ? "#0088FF" : "#FF4560";
  const width = `${score}%`;
  return (
    <div className="flex items-center gap-2 h-full">
      <div className="flex-1 h-1.5 rounded-full bg-oxford overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width, background: color }}
        />
      </div>
      <span className="font-mono text-xs font-bold min-w-[28px]" style={{ color }}>
        {score.toFixed(0)}
      </span>
    </div>
  );
}

function SparklineCellRenderer({ value }: ICellRendererParams) {
  const data = value as number[];
  if (!data || data.length < 2) return <span className="text-muted text-xs">—</span>;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  // Render SVG
  const width = 100;
  const height = 24;
  
  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((val - min) / range) * height;
    return `${x},${y}`;
  }).join(" ");

  const isUp = data[data.length - 1] >= data[0];
  const color = isUp ? "#00FF87" : "#FF4560";

  return (
    <div className="flex items-center h-full w-full py-1">
      <svg width={width} height={height} className="overflow-visible">
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}

function TickerCellRenderer({ value, data }: ICellRendererParams) {
  const row = data as TickerValidation;
  return (
    <div className="flex items-center gap-1.5">
      <span className="font-mono font-bold text-neon-green text-xs">{value}</span>
      {row.fundamentals.low_institutional_coverage && (
        <span className="px-1 py-0.5 rounded text-[9px] font-mono bg-electric-blue/10 text-electric-blue border border-electric-blue/20">
          GEM
        </span>
      )}
    </div>
  );
}

// ── Filter input components ────────────────────────────────────────────────
interface FilterInputProps {
  label: string;
  value: number | null | undefined;
  onChange: (val: number | null) => void;
  min?: number;
  max?: number;
  step?: number;
  suffix?: string;
  info?: string;
}

function FilterInput({
  label,
  value,
  onChange,
  min = 0,
  max = 1000,
  step = 1,
  suffix = "",
  info,
}: FilterInputProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-mono text-muted">{label}</label>
      {info && <span className="text-[10px] text-muted/60 italic">{info}</span>}
      <div className="flex items-center gap-2">
        <input
          type="number"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value ? parseFloat(e.target.value) : null)}
          placeholder="—"
          min={min}
          max={max}
          step={step}
          className="w-full px-2 py-1.5 bg-oxford/50 border border-border rounded text-xs font-mono text-text-primary placeholder-muted/40 focus:outline-none focus:border-electric-blue/50"
        />
        {suffix && <span className="text-xs text-muted whitespace-nowrap">{suffix}</span>}
      </div>
    </div>
  );
}

interface FilterRangeProps {
  label: string;
  minValue: number | null | undefined;
  maxValue: number | null | undefined;
  onMinChange: (val: number | null) => void;
  onMaxChange: (val: number | null) => void;
  min?: number;
  max?: number;
  step?: number;
  suffix?: string;
  info?: string;
}

function FilterRange({
  label,
  minValue,
  maxValue,
  onMinChange,
  onMaxChange,
  min = 0,
  max = 1000,
  step = 1,
  suffix = "",
  info,
}: FilterRangeProps) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-mono text-muted">{label}</label>
      {info && <span className="text-[10px] text-muted/60 italic">{info}</span>}
      <div className="flex items-center gap-2">
        <input
          type="number"
          value={minValue ?? ""}
          onChange={(e) => onMinChange(e.target.value ? parseFloat(e.target.value) : null)}
          placeholder="Min"
          min={min}
          max={max}
          step={step}
          className="w-1/2 px-2 py-1.5 bg-oxford/50 border border-border rounded text-xs font-mono text-text-primary placeholder-muted/40 focus:outline-none focus:border-electric-blue/50"
        />
        <span className="text-xs text-muted">to</span>
        <input
          type="number"
          value={maxValue ?? ""}
          onChange={(e) => onMaxChange(e.target.value ? parseFloat(e.target.value) : null)}
          placeholder="Max"
          min={min}
          max={max}
          step={step}
          className="w-1/2 px-2 py-1.5 bg-oxford/50 border border-border rounded text-xs font-mono text-text-primary placeholder-muted/40 focus:outline-none focus:border-electric-blue/50"
        />
        {suffix && <span className="text-xs text-muted whitespace-nowrap">{suffix}</span>}
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────
export default function AdvancedScreener() {
  const [rows, setRows] = useState<TickerValidation[]>([]);
  const [loading, setLoading] = useState(false);
  const [tickers, setTickers] = useState(
    "ASTS,IONQ,LUNR,RKLB,ACHR,JOBY,HLLY,AIOT,SMAR,BRZE,PLTR,NVDA,AXON,CELH,DUOL,MNDY"
  );
  const [filters, setFilters] = useState<ScreenerFilters>(DEFAULT_FILTERS);
  const [expandedSections, setExpandedSections] = useState<
    Record<string, boolean>
  >({
    valuacion: true,
    crecimiento: true,
    rentabilidad: true,
    balanceSheet: true,
    liquidez: true,
    calidad: true,
  });

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const handleSearch = useCallback(async () => {
    if (!tickers.trim()) {
      toast.error("Please enter at least one ticker");
      return;
    }

    setLoading(true);
    try {
      const data = await api.advancedScreener(tickers, filters);
      setRows(data);

      const wideMoat = data.filter((d) => d.fundamentals.moat === "Wide");
      const buyZone = data.filter((d) => d.recommendation === "STRONG_BUY" || d.recommendation === "BUY");

      toast.success(
        `Found ${data.length} results${wideMoat.length > 0 ? ` (${wideMoat.length} Wide Moat)` : ""}${
          buyZone.length > 0 ? ` (${buyZone.length} Buy Zone)` : ""
        }`
      );
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to run screener");
    } finally {
      setLoading(false);
    }
  }, [tickers, filters]);

  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_FILTERS);
  }, []);

  const applyPreset = useCallback((presetName: string) => {
    const preset = GURU_SCREENS[presetName];
    if (preset) {
      setFilters((prev) => ({ ...prev, ...preset }));
      toast.info(`Applied ${presetName} screen`);
    }
  }, []);

  const columnDefs: any[] = useMemo(
    () => [
      {
        headerName: "TICKER",
        field: "ticker",
        width: 110,
        pinned: "left",
        cellRenderer: TickerCellRenderer,
        sortable: true,
        filter: true,
      },
      {
        headerName: "COMPANY",
        valueGetter: (p: any) => p.data?.fundamentals.company_name,
        width: 180,
        sortable: true,
        filter: true,
        cellStyle: { color: "#A0AECB", fontSize: "11px" },
      },
      {
        headerName: "SECTOR",
        valueGetter: (p: any) => p.data?.fundamentals.sector ?? "—",
        width: 130,
        sortable: true,
        filter: true,
        cellStyle: { color: "#6B7A99", fontSize: "11px" },
      },
      {
        headerName: "TREND (20D)",
        valueGetter: (p: any) => p.data?.fundamentals.price_history_20d ?? null,
        cellRenderer: SparklineCellRenderer,
        width: 140,
        sortable: false,
        filter: false,
      },
      {
        headerName: "MOAT",
        valueGetter: (p: any) => p.data?.fundamentals.moat,
        width: 90,
        sortable: true,
        cellRenderer: MoatCellRenderer,
      },
      {
        headerName: "ALPHA",
        valueGetter: (p: any) => p.data?.alpha_score.total ?? 0,
        width: 120,
        sortable: true,
        sort: "desc",
        cellRenderer: ScoreCellRenderer,
      },
      {
        headerName: "REC",
        valueGetter: (p: any) => p.data?.recommendation,
        width: 120,
        sortable: true,
        cellRenderer: RecCellRenderer,
      },
      {
        headerName: "REV GROWTH",
        valueGetter: (p: any) => p.data?.fundamentals.revenue_growth_yoy ?? null,
        width: 110,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          fmtPct(p.value as number, true),
        cellStyle: (params: any) => ({
          color:
            (params.value as number) >= 0.2
              ? "#00FF87"
              : (params.value as number) >= 0
              ? "#E8EBF0"
              : "#FF4560",
          fontFamily: "'JetBrains Mono'",
          fontSize: "12px",
          fontWeight: 600,
        }),
      },
      {
        headerName: "MKT CAP",
        valueGetter: (p: any) => p.data?.fundamentals.market_cap ?? null,
        width: 110,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) => fmtCap(p.value as number | null),
        cellStyle: { color: "#A0AECB", fontFamily: "'JetBrains Mono'", fontSize: "12px" },
      },
      {
        headerName: "PE",
        valueGetter: (p: any) => p.data?.fundamentals.pe_ratio ?? null,
        width: 80,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          p.value != null ? p.value.toFixed(1) : "—",
        cellStyle: { color: "#A0AECB", fontFamily: "'JetBrains Mono'", fontSize: "12px" },
      },
      {
        headerName: "NET MARGIN",
        valueGetter: (p: any) => p.data?.fundamentals.net_margin ?? null,
        width: 110,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          fmtPct(p.value as number, true),
        cellStyle: (params: any) => ({
          color: (params.value as number) >= 0 ? "#00FF87" : "#FF4560",
          fontFamily: "'JetBrains Mono'",
          fontSize: "12px",
        }),
      },
      {
        headerName: "ROE",
        valueGetter: (p: any) => p.data?.fundamentals.roe ?? null,
        width: 80,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          fmtPct(p.value as number, true),
        cellStyle: { color: "#A0AECB", fontFamily: "'JetBrains Mono'", fontSize: "12px" },
      },
      {
        headerName: "D/E",
        valueGetter: (p: any) => p.data?.fundamentals.debt_to_equity ?? null,
        width: 80,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          p.value != null ? p.value.toFixed(2) : "—",
        cellStyle: (params: any) => ({
          color: (params.value as number) < 1.5 ? "#00FF87" : "#FF4560",
          fontFamily: "'JetBrains Mono'",
          fontSize: "12px",
        }),
      },
      {
        headerName: "FCF YIELD",
        valueGetter: (p: any) => p.data?.fundamentals.fcf_yield ?? null,
        width: 100,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          fmtPct(p.value as number, true),
        cellStyle: (params: any) => ({
          color: (params.value as number) >= 0.03 ? "#00FF87" : "#FF4560",
          fontFamily: "'JetBrains Mono'",
          fontSize: "12px",
        }),
      },
      {
        headerName: "PIOTROSKI",
        valueGetter: (p: any) => p.data?.fundamentals.piotroski_f_score ?? null,
        width: 100,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          p.value != null ? `${p.value}/9` : "—",
        cellStyle: (params: any) => ({
          color: (params.value as number) >= 7 ? "#00FF87" : (params.value as number) >= 5 ? "#E8EBF0" : "#FF4560",
          fontFamily: "'JetBrains Mono'",
          fontSize: "12px",
          fontWeight: "bold"
        }),
      },
      {
        headerName: "ALTMAN Z",
        valueGetter: (p: any) => p.data?.fundamentals.altman_z_score ?? null,
        width: 100,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          p.value != null ? p.value.toFixed(2) : "—",
        cellStyle: (params: any) => ({
          color: (params.value as number) >= 3 ? "#00FF87" : "#FF4560",
          fontFamily: "'JetBrains Mono'",
          fontSize: "12px",
        }),
      },
      {
        headerName: "INST OWN",
        valueGetter: (p: any) => p.data?.fundamentals.institutional_ownership_pct ?? null,
        width: 100,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          p.value != null ? `${Number(p.value).toFixed(1)}%` : "—",
        cellStyle: (params: any) => ({
          color: (params.value as number) < 40 ? "#0088FF" : "#6B7A99",
          fontFamily: "'JetBrains Mono'",
          fontSize: "12px",
        }),
      },
    ],
    []
  );

  const getRowStyle = useCallback((params: RowClassParams<TickerValidation>) => {
    if (
      params.data?.fundamentals.moat === "Wide" &&
      (params.data?.recommendation === "STRONG_BUY" || params.data?.recommendation === "BUY")
    ) {
      return { borderLeft: "3px solid #00FF87", background: "rgba(0,255,135,0.03)" };
    }
    return undefined;
  }, []);

  // ── Collapsible filter section ─────────────────────────────────────────
  interface FilterSectionProps {
    title: string;
    id: string;
    children: React.ReactNode;
  }

  const FilterSection = ({ title, id, children }: FilterSectionProps) => (
    <div className="border border-border/50 rounded-lg overflow-hidden bg-oxford/30 backdrop-blur-md transition-colors hover:bg-oxford/40">
      <button
        onClick={() => toggleSection(id)}
        className="w-full px-4 py-3 hover:bg-white/[0.02] transition-colors flex items-center justify-between"
      >
        <span className="text-[11px] font-mono font-bold tracking-wider text-text-primary uppercase">{title}</span>
        {expandedSections[id] ? (
          <ChevronUp className="w-4 h-4 text-electric-blue" />
        ) : (
          <ChevronDown className="w-4 h-4 text-muted" />
        )}
      </button>
      <AnimatePresence>
        {expandedSections[id] && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="p-4 bg-black/20 border-t border-border/50 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="flex flex-col gap-6"
    >
      {/* ── Filters Panel ────────────────────────────────────────────────── */}
      <div className="card p-5 flex flex-col gap-5 border border-white/5 shadow-2xl relative overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-electric-blue/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-neon-green/5 rounded-full blur-3xl pointer-events-none" />
        
        <div className="flex items-center justify-between relative z-10">
          <div className="flex items-center gap-3">
            <span className="text-sm font-mono font-bold tracking-widest text-white/90 uppercase border-l-2 border-electric-blue pl-3">
              Advanced Screener
            </span>
          </div>
          <button
            onClick={resetFilters}
            className="p-1.5 rounded border border-border text-muted hover:text-electric-blue hover:border-electric-blue/30 transition-all"
            title="Reset to defaults"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Guru Screens Presets */}
        <div className="flex flex-col gap-3 border-b border-border/50 pb-5 relative z-10">
          <label className="text-xs font-mono text-electric-blue flex items-center gap-2">
            <span className="animate-pulse">✨</span> 
            <span className="font-bold tracking-wider">GURU SCREENS</span>
            <span className="text-[10px] text-muted italic ml-2 bg-oxford/50 px-2 py-0.5 rounded-full">1-click institutional presets</span>
          </label>
          <div className="flex flex-wrap gap-3">
            {Object.keys(GURU_SCREENS).map((name, i) => (
              <motion.button
                whileHover={{ scale: 1.02, boxShadow: "0 0 15px rgba(0, 136, 255, 0.4)" }}
                whileTap={{ scale: 0.98 }}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                key={name}
                onClick={() => applyPreset(name)}
                className="px-4 py-2 rounded-md text-[11px] font-mono bg-gradient-to-r from-oxford to-[#1c273e] border border-electric-blue/30 text-white hover:border-electric-blue shadow-lg hover:shadow-electric-blue/20 transition-all relative overflow-hidden group"
              >
                <span className="relative z-10">{name}</span>
                <div className="absolute inset-0 bg-gradient-to-r from-electric-blue/0 via-electric-blue/10 to-electric-blue/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000 ease-in-out" />
              </motion.button>
            ))}
          </div>
        </div>

        {/* Universe input */}
        <div className="flex flex-col gap-2">
          <label className="text-xs font-mono text-muted">TICKER UNIVERSE</label>
          <textarea
            value={tickers}
            onChange={(e) => setTickers(e.target.value)}
            placeholder="Enter comma-separated tickers (max 25)"
            className="w-full px-3 py-2 bg-oxford/50 border border-border rounded text-xs font-mono text-text-primary placeholder-muted/40 focus:outline-none focus:border-electric-blue/50 resize-none"
            rows={2}
          />
        </div>

        {/* Valuación */}
        <FilterSection title="VALUACIÓN (Valuation)" id="valuacion">
          <>
            <FilterInput
              label="P/E Max"
              value={filters.pe_max}
              onChange={(val) => setFilters({ ...filters, pe_max: val })}
              min={5}
              max={150}
              step={1}
              info="Price-to-Earnings ratio"
            />
            <FilterInput
              label="P/S Max"
              value={filters.ps_max}
              onChange={(val) => setFilters({ ...filters, ps_max: val })}
              min={0.1}
              max={10}
              step={0.1}
              info="Price-to-Sales ratio"
            />
            <FilterInput
              label="PEG Max"
              value={filters.peg_max}
              onChange={(val) => setFilters({ ...filters, peg_max: val })}
              min={0.5}
              max={3}
              step={0.1}
              info="P/E divided by growth %"
            />
            <FilterInput
              label="EV/EBITDA Max"
              value={filters.ev_ebitda_max}
              onChange={(val) => setFilters({ ...filters, ev_ebitda_max: val })}
              min={2}
              max={30}
              step={1}
              info="Enterprise value/EBITDA"
            />
          </>
        </FilterSection>

        {/* Crecimiento */}
        <FilterSection title="CRECIMIENTO (Growth)" id="crecimiento">
          <>
            <FilterInput
              label="Rev Growth Min"
              value={filters.revenue_growth_min ? filters.revenue_growth_min * 100 : undefined}
              onChange={(val) =>
                setFilters({ ...filters, revenue_growth_min: val ? val / 100 : null })
              }
              min={0}
              max={300}
              step={5}
              suffix="%"
              info="YoY revenue growth"
            />
            <FilterInput
              label="Earnings Growth Min"
              value={
                filters.earnings_growth_min ? filters.earnings_growth_min * 100 : undefined
              }
              onChange={(val) =>
                setFilters({ ...filters, earnings_growth_min: val ? val / 100 : null })
              }
              min={0}
              max={300}
              step={5}
              suffix="%"
              info="YoY earnings growth"
            />
            <FilterInput
              label="3Y CAGR Min"
              value={
                filters.revenue_cagr_3y_min ? filters.revenue_cagr_3y_min * 100 : undefined
              }
              onChange={(val) =>
                setFilters({ ...filters, revenue_cagr_3y_min: val ? val / 100 : null })
              }
              min={0}
              max={100}
              step={5}
              suffix="%"
              info="3-year compound annual growth"
            />
          </>
        </FilterSection>

        {/* Rentabilidad */}
        <FilterSection title="RENTABILIDAD (Profitability)" id="rentabilidad">
          <>
            <FilterInput
              label="Gross Margin Min"
              value={filters.gross_margin_min ? filters.gross_margin_min * 100 : undefined}
              onChange={(val) =>
                setFilters({ ...filters, gross_margin_min: val ? val / 100 : null })
              }
              min={0}
              max={100}
              step={5}
              suffix="%"
              info="Gross profit margin"
            />
            <FilterInput
              label="Operating Margin Min"
              value={
                filters.operating_margin_min ? filters.operating_margin_min * 100 : undefined
              }
              onChange={(val) =>
                setFilters({ ...filters, operating_margin_min: val ? val / 100 : null })
              }
              min={0}
              max={50}
              step={2}
              suffix="%"
              info="Operating profit margin"
            />
            <FilterInput
              label="Net Margin Min"
              value={filters.net_margin_min ? filters.net_margin_min * 100 : undefined}
              onChange={(val) =>
                setFilters({ ...filters, net_margin_min: val ? val / 100 : null })
              }
              min={-20}
              max={50}
              step={2}
              suffix="%"
              info="Net profit margin"
            />
            <FilterInput
              label="ROE Min"
              value={filters.roe_min ? filters.roe_min * 100 : undefined}
              onChange={(val) => setFilters({ ...filters, roe_min: val ? val / 100 : null })}
              min={0}
              max={100}
              step={5}
              suffix="%"
              info="Return on equity"
            />
            <FilterInput
              label="ROA Min"
              value={filters.roa_min ? filters.roa_min * 100 : undefined}
              onChange={(val) => setFilters({ ...filters, roa_min: val ? val / 100 : null })}
              min={0}
              max={100}
              step={5}
              suffix="%"
              info="Return on assets"
            />
          </>
        </FilterSection>

        {/* Balance Sheet */}
        <FilterSection title="BALANCE SHEET (Debt & Liquidity)" id="balanceSheet">
          <>
            <FilterInput
              label="D/E Max"
              value={filters.debt_to_equity_max}
              onChange={(val) => setFilters({ ...filters, debt_to_equity_max: val })}
              min={0}
              max={5}
              step={0.1}
              info="Debt-to-equity ratio"
            />
            <FilterInput
              label="Debt/FCF Max"
              value={filters.debt_to_fcf_max}
              onChange={(val) => setFilters({ ...filters, debt_to_fcf_max: val })}
              min={0}
              max={10}
              step={0.5}
              info="Total Debt to FCF ratio"
            />
            <FilterInput
              label="Current Ratio Min"
              value={filters.current_ratio_min}
              onChange={(val) => setFilters({ ...filters, current_ratio_min: val })}
              min={0.5}
              max={3}
              step={0.1}
              info="Current assets/liabilities"
            />
            <FilterInput
              label="Interest Coverage Min"
              value={filters.interest_coverage_min}
              onChange={(val) => setFilters({ ...filters, interest_coverage_min: val })}
              min={0}
              max={20}
              step={1}
              info="EBIT / Interest expense"
            />
          </>
        </FilterSection>

        {/* Liquidez */}
        <FilterSection title="LIQUIDEZ & TAMAÑO (Size & Liquidity)" id="liquidez">
          <>
            <FilterInput
              label="Market Cap Min"
              value={filters.market_cap_min ? filters.market_cap_min / 1e6 : undefined}
              onChange={(val) =>
                setFilters({ ...filters, market_cap_min: val ? val * 1e6 : null })
              }
              min={0}
              max={500}
              step={10}
              suffix="M"
              info="Minimum market cap ($M)"
            />
            <FilterInput
              label="Market Cap Max"
              value={filters.market_cap_max ? filters.market_cap_max / 1e9 : undefined}
              onChange={(val) =>
                setFilters({ ...filters, market_cap_max: val ? val * 1e9 : null })
              }
              min={0.1}
              max={10}
              step={0.5}
              suffix="B"
              info="Maximum market cap ($B)"
            />
            <FilterInput
              label="Short Interest Max"
              value={filters.short_interest_max ? filters.short_interest_max * 100 : undefined}
              onChange={(val) =>
                setFilters({ ...filters, short_interest_max: val ? val / 100 : null })
              }
              min={0}
              max={50}
              step={2}
              suffix="%"
              info="Max short float %"
            />
          </>
        </FilterSection>

        {/* Calidad */}
        <FilterSection title="CALIDAD (Quality)" id="calidad">
          <>
            <FilterInput
              label="FCF Yield Min"
              value={filters.fcf_yield_min ? filters.fcf_yield_min * 100 : undefined}
              onChange={(val) => setFilters({ ...filters, fcf_yield_min: val ? val / 100 : null })}
              min={0}
              max={50}
              step={1}
              suffix="%"
              info="Free Cash Flow Yield"
            />
            <FilterInput
              label="Piotroski Score Min"
              value={filters.piotroski_f_score_min}
              onChange={(val) => setFilters({ ...filters, piotroski_f_score_min: val })}
              min={0}
              max={9}
              step={1}
              info="Financial quality (0-9)"
            />
            <FilterInput
              label="Altman Z-Score Min"
              value={filters.altman_z_score_min}
              onChange={(val) => setFilters({ ...filters, altman_z_score_min: val })}
              min={0}
              max={10}
              step={0.5}
              info="Bankruptcy safety score (>3)"
            />
            <FilterInput
              label="Inst Ownership Min"
              value={
                filters.institutional_ownership_min
                  ? filters.institutional_ownership_min * 100
                  : undefined
              }
              onChange={(val) =>
                setFilters({
                  ...filters,
                  institutional_ownership_min: val ? val / 100 : null,
                })
              }
              min={0}
              max={100}
              step={5}
              suffix="%"
              info="Minimum institutional ownership"
            />
            <FilterInput
              label="Inst Ownership Max"
              value={
                filters.institutional_ownership_max
                  ? filters.institutional_ownership_max * 100
                  : undefined
              }
              onChange={(val) =>
                setFilters({
                  ...filters,
                  institutional_ownership_max: val ? val / 100 : null,
                })
              }
              min={0}
              max={100}
              step={5}
              suffix="%"
              info="Maximum institutional ownership"
            />
            <FilterInput
              label="Alpha Score Min"
              value={filters.alpha_score_min}
              onChange={(val) => setFilters({ ...filters, alpha_score_min: val })}
              min={0}
              max={100}
              step={5}
              info="Minimum Alpha Score"
            />
          </>
        </FilterSection>

        {/* Action buttons */}
        <div className="flex justify-end pt-4 border-t border-border/50 relative z-10 mt-2">
          <motion.button
            whileHover={{ scale: 1.02, boxShadow: "0 0 20px rgba(0, 255, 135, 0.4)" }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSearch}
            disabled={loading}
            className={clsx(
              "w-full md:w-auto px-8 py-3 rounded-lg font-mono text-sm font-bold tracking-widest transition-all relative overflow-hidden group flex justify-center",
              loading
                ? "bg-oxford text-muted border border-border cursor-not-allowed"
                : "bg-gradient-to-r from-[#00b35e] to-neon-green text-oxford border-none shadow-lg hover:shadow-neon-green/30"
            )}
          >
            {loading ? (
              <div className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>PROCESSING...</span>
              </div>
            ) : (
              <>
                <span className="relative z-10 flex items-center gap-2">
                  <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
                  RUN INSTITUTIONAL SCREENER
                </span>
                <div className="absolute inset-0 bg-white/20 translate-y-[100%] group-hover:translate-y-[0%] transition-transform duration-300 ease-out" />
              </>
            )}
          </motion.button>
        </div>
      </div>

      {/* ── Results Table ────────────────────────────────────────────────── */}
      <AnimatePresence>
        {rows.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2, ease: "easeOut" }}
            className="card p-0 flex flex-col border border-white/5 shadow-2xl relative overflow-hidden backdrop-blur-xl bg-oxford/40"
          >
            {/* Header */}
            <div className="p-4 border-b border-border/50 flex items-center justify-between bg-black/20">
              <div className="flex items-center gap-3">
                <span className="text-sm font-mono font-bold tracking-widest text-white/90 uppercase border-l-2 border-neon-green pl-3">
                  SCREENER RESULTS
                </span>
                <span className="px-2.5 py-1 rounded bg-neon-green/10 text-[10px] font-mono text-neon-green border border-neon-green/20 font-bold">
                  {rows.length} MATCHES
                </span>
              </div>
            </div>

            {/* Stats row */}
            <div className="flex gap-4 text-xs font-mono flex-wrap p-4 bg-oxford/20">
              {[
                { label: "Total", value: rows.length, color: "text-text-secondary" },
                {
                  label: "Wide Moat",
                  value: rows.filter((r) => r.fundamentals.moat === "Wide").length,
                  color: "text-neon-green",
                },
                {
                  label: "Buy Zone",
                  value: rows.filter((r) => r.recommendation === "STRONG_BUY" || r.recommendation === "BUY").length,
                  color: "text-neon-green",
                },
                {
                  label: "Avg Alpha",
                  value: (
                    rows.reduce((s, r) => s + (r.alpha_score?.total ?? 0), 0) / rows.length
                  ).toFixed(1),
                  color: "text-electric-blue",
                },
              ].map(({ label, value, color }) => (
                <div key={label} className="flex items-center gap-1.5 bg-black/20 px-3 py-1.5 rounded-md border border-border/50">
                  <span className="text-muted">{label}:</span>
                  <span className={clsx("font-bold", color)}>{value}</span>
                </div>
              ))}
            </div>

            {/* AG Grid */}
            <div className="ag-theme-alpine-dark w-full" style={{ height: 500 }}>
              <AgGridReact<TickerValidation>
                rowData={rows}
                columnDefs={columnDefs}
                defaultColDef={{
                  resizable: true,
                  sortable: true,
                  filter: false,
                  suppressMovable: false,
                }}
                rowHeight={44}
                headerHeight={40}
                animateRows
                getRowStyle={getRowStyle}
                suppressCellFocus
                enableCellTextSelection
                pagination
                paginationPageSize={15}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Empty state */}
      {!loading && rows.length === 0 && (
        <div className="card p-12 text-center flex flex-col items-center justify-center gap-3">
          <span className="text-3xl">🔎</span>
          <p className="text-sm text-muted font-mono">
            Enter tickers and adjust filters to run screener
          </p>
        </div>
      )}
    </motion.div>
  );
}
