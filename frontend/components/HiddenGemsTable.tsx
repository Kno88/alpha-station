"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { AgGridReact } from "ag-grid-react";
import type {
  ColDef,
  ICellRendererParams,
  ValueFormatterParams,
  RowClassParams,
} from "ag-grid-community";
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-alpine.css";
import { api, TickerValidation, fmtCap, fmtPct, stageColor, recColor } from "@/lib/api";
import { toast } from "react-toastify";
import { RefreshCw, Loader2, Download, SlidersHorizontal } from "lucide-react";
import clsx from "clsx";

// ── Cell renderers ─────────────────────────────────────────────────────────────

function StageCellRenderer({ value }: ICellRendererParams) {
  const color = stageColor(value as string);
  return (
    <span
      className="inline-block px-2 py-0.5 rounded text-xs font-mono font-semibold"
      style={{
        color,
        background: color + "15",
        border: `1px solid ${color}30`,
      }}
    >
      {value}
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

function RvolCellRenderer({ value }: ICellRendererParams) {
  const rvol = value as number;
  const isAlert = rvol >= 2.5;
  return (
    <span
      className={clsx(
        "font-mono text-xs font-semibold",
        isAlert ? "text-neon-green animate-pulse" : "text-text-secondary"
      )}
    >
      {rvol.toFixed(2)}x{isAlert && " 🚀"}
    </span>
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

// ── Universe presets ───────────────────────────────────────────────────────────
const UNIVERSE_PRESETS: Record<string, string> = {
  "Hidden Gems":    "ASTS,IONQ,RKLB,ACHR,SMAR",
  "Growth Leaders": "NVDA,AXON,CELH,DUOL,MNDY",
  "Small Cap Alpha": "ASTS,IONQ,RKLB,PLTR,BRZE",
};

// ── Main Component ────────────────────────────────────────────────────────────
export default function HiddenGemsTable() {
  const [rows, setRows] = useState<TickerValidation[]>([]);
  const [loading, setLoading] = useState(true);
  const [preset, setPreset] = useState("Hidden Gems");
  const [stageFilter, setStageFilter] = useState<string>("all");

  const fetchData = useCallback(async (tickers: string) => {
    setLoading(true);
    try {
      const data = await api.hiddenGems(tickers);
      setRows(data);

      const s2 = data.filter((d) => d.stage.stage === "Stage 2");
      if (s2.length > 0) {
        toast.success(`🚀 ${s2.length} Hidden Gem(s) in Stage 2!`);
      }
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Failed to load screener");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(UNIVERSE_PRESETS[preset]);
  }, [preset, fetchData]);

  const filteredRows = useMemo(() => {
    if (stageFilter === "all") return rows;
    return rows.filter((r) => r.stage.stage === stageFilter);
  }, [rows, stageFilter]);

  // ── AG Grid column definitions ─────────────────────────────────────────────
  const columnDefs: ColDef<TickerValidation>[] = useMemo(
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
        valueGetter: (p) => p.data?.fundamentals.company_name,
        width: 180,
        sortable: true,
        filter: true,
        cellStyle: { color: "#A0AECB", fontSize: "11px", fontFamily: "inherit" },
      },
      {
        headerName: "SECTOR",
        valueGetter: (p) => p.data?.fundamentals.sector ?? "—",
        width: 130,
        sortable: true,
        filter: true,
        cellStyle: { color: "#6B7A99", fontSize: "11px", fontFamily: "inherit" },
      },
      {
        headerName: "STAGE",
        valueGetter: (p) => p.data?.stage.stage,
        width: 110,
        sortable: true,
        filter: true,
        cellRenderer: StageCellRenderer,
      },
      {
        headerName: "ALPHA SCORE",
        valueGetter: (p) => p.data?.alpha_score.total ?? 0,
        width: 150,
        sortable: true,
        sort: "desc",
        cellRenderer: ScoreCellRenderer,
      },
      {
        headerName: "RECOMMENDATION",
        valueGetter: (p) => p.data?.recommendation,
        width: 150,
        sortable: true,
        cellRenderer: RecCellRenderer,
      },
      {
        headerName: "RVOL",
        valueGetter: (p) => p.data?.liquidity.rvol ?? 0,
        width: 100,
        sortable: true,
        cellRenderer: RvolCellRenderer,
      },
      {
        headerName: "PRICE",
        valueGetter: (p) => p.data?.stage.price ?? 0,
        width: 90,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          `$${Number(p.value).toFixed(2)}`,
        cellStyle: { color: "#E8EBF0", fontFamily: "'JetBrains Mono'", fontSize: "12px" },
      },
      {
        headerName: "REV GROWTH",
        valueGetter: (p) => p.data?.fundamentals.revenue_growth_yoy ?? null,
        width: 120,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          fmtPct(p.value as number, true),
        cellStyle: (params) => ({
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
        valueGetter: (p) => p.data?.fundamentals.market_cap ?? null,
        width: 110,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) => fmtCap(p.value as number | null),
        cellStyle: { color: "#A0AECB", fontFamily: "'JetBrains Mono'", fontSize: "12px" },
      },
      {
        headerName: "NET MARGIN",
        valueGetter: (p) => p.data?.fundamentals.net_margin ?? null,
        width: 120,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          fmtPct(p.value as number, true),
        cellStyle: (params) => ({
          color: (params.value as number) >= 0 ? "#00FF87" : "#FF4560",
          fontFamily: "'JetBrains Mono'",
          fontSize: "12px",
        }),
      },
      {
        headerName: "INST OWN",
        valueGetter: (p) => p.data?.fundamentals.institutional_ownership_pct ?? null,
        width: 100,
        sortable: true,
        valueFormatter: (p: ValueFormatterParams) =>
          p.value != null ? `${Number(p.value).toFixed(1)}%` : "—",
        cellStyle: (params) => ({
          color: (params.value as number) < 40 ? "#0088FF" : "#6B7A99",
          fontFamily: "'JetBrains Mono'",
          fontSize: "12px",
        }),
      },
      {
        headerName: "MA ALIGN",
        valueGetter: (p) => (p.data?.stage.ma_alignment ? "Yes" : "No"),
        width: 90,
        sortable: true,
        cellStyle: (params) => ({
          color: params.value === "Yes" ? "#00FF87" : "#FF4560",
          fontFamily: "'JetBrains Mono'",
          fontSize: "12px",
          fontWeight: 600,
        }),
      },
    ],
    []
  );

  // Highlight Stage 2 rows
  const getRowStyle = useCallback((params: RowClassParams<TickerValidation>) => {
    if (params.data?.stage.stage === "Stage 2" && params.data?.liquidity.rvol >= 2.5) {
      return { borderLeft: "3px solid #00FF87", background: "rgba(0,255,135,0.03)" };
    }
    return undefined;
  }, []);

  return (
    <div className="card p-5 flex flex-col gap-4">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <span className="card-header">◈ HIDDEN GEMS SCREENER</span>
          <p className="text-xs text-muted mt-0.5">
            Small/Mid Caps · Low Institutional Coverage · High Growth
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {/* Stage filter */}
          <div className="flex items-center gap-1">
            <SlidersHorizontal className="w-3.5 h-3.5 text-muted" />
            {["all", "Stage 1", "Stage 2", "Stage 3", "Stage 4"].map((s) => (
              <button
                key={s}
                onClick={() => setStageFilter(s)}
                className={clsx(
                  "px-2 py-0.5 rounded text-xs font-mono transition-all",
                  stageFilter === s
                    ? "bg-electric-blue/15 text-electric-blue border border-electric-blue/30"
                    : "text-muted border border-border hover:border-electric-blue/20"
                )}
              >
                {s === "all" ? "All" : s.replace("Stage ", "S")}
              </button>
            ))}
          </div>

          {/* Preset selector */}
          {Object.keys(UNIVERSE_PRESETS).map((p) => (
            <button
              key={p}
              onClick={() => setPreset(p)}
              className={clsx(
                "px-2.5 py-1 rounded text-xs font-mono transition-all",
                preset === p
                  ? "bg-neon-green/10 text-neon-green border border-neon-green/30"
                  : "text-muted border border-border hover:border-neon-green/20"
              )}
            >
              {p}
            </button>
          ))}

          <button
            onClick={() => fetchData(UNIVERSE_PRESETS[preset])}
            disabled={loading}
            className="p-1.5 rounded border border-border text-muted hover:text-electric-blue hover:border-electric-blue/30 transition-all disabled:opacity-40"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* ── Stats row ───────────────────────────────────────────────────── */}
      <div className="flex gap-4 text-xs font-mono">
        {[
          { label: "Total", value: filteredRows.length, color: "text-text-secondary" },
          {
            label: "Stage 2",
            value: filteredRows.filter((r) => r.stage.stage === "Stage 2").length,
            color: "text-neon-green",
          },
          {
            label: "Buy Zone",
            value: filteredRows.filter((r) => r.recommendation === "BUY_ZONE").length,
            color: "text-neon-green",
          },
          {
            label: "RVOL Alert",
            value: filteredRows.filter((r) => r.liquidity.rvol >= 2.5).length,
            color: "text-amber",
          },
        ].map(({ label, value, color }) => (
          <div key={label} className="flex items-center gap-1.5">
            <span className="text-muted">{label}:</span>
            <span className={clsx("font-bold", color)}>{value}</span>
          </div>
        ))}
      </div>

      {/* ── AG Grid ─────────────────────────────────────────────────────── */}
      {loading ? (
        <div className="flex items-center justify-center h-48 gap-2">
          <Loader2 className="w-5 h-5 text-electric-blue animate-spin" />
          <span className="text-xs text-muted font-mono">Screening universe...</span>
        </div>
      ) : (
        <div className="ag-theme-alpine-dark" style={{ height: 420, width: "100%" }}>
          <AgGridReact<TickerValidation>
            rowData={filteredRows}
            columnDefs={columnDefs}
            defaultColDef={{
              resizable: true,
              sortable: true,
              filter: false,
              suppressMovable: false,
            }}
            rowHeight={44}
            headerHeight={36}
            animateRows
            getRowStyle={getRowStyle}
            suppressCellFocus
            enableCellTextSelection
            pagination
            paginationPageSize={10}
          />
        </div>
      )}
    </div>
  );
}
