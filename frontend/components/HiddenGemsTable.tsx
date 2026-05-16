"use client";

import { useMemo } from "react";
import { AgGridReact } from "ag-grid-react";
import { 
  ColDef, 
  ValueFormatterParams,
  RowClassParams 
} from "ag-grid-community";
import { 
  TrendingUp, 
  Gem, 
  ArrowUpRight,
  Activity,
  Layers
} from "lucide-react";
import useSWR from "swr";
import { 
  api, 
  TickerValidation, 
  fmtPct, 
  fmtCap,
  recColor
} from "@/lib/api";
import clsx from "clsx";
import { motion } from "framer-motion";

export default function HiddenGemsTable() {
  const { data: rows = [], isLoading } = useSWR<TickerValidation[]>(
    "/api/hidden-gems",
    () => api.hiddenGems()
  );

  const columnDefs = useMemo<ColDef<TickerValidation>[]>(
    () => [
      {
        headerName: "TICKER",
        field: "ticker",
        width: 120,
        pinned: "left",
        cellRenderer: (p: any) => (
          <div className="flex items-center gap-2 h-full">
            <span className="font-mono font-black text-neon-green tracking-tighter">{p.value}</span>
            <ArrowUpRight className="w-3 h-3 text-muted/50" />
          </div>
        ),
      },
      {
        headerName: "ALPHA GRADE",
        valueGetter: (p) => p.data?.alpha_score.grade,
        width: 120,
        cellRenderer: (p: any) => (
          <div className="flex items-center justify-center h-full">
            <span className={clsx(
              "px-3 py-1 rounded-full text-[10px] font-mono font-black tracking-widest border",
              p.value === 'A' ? "bg-neon-green/10 text-neon-green border-neon-green/30 shadow-[0_0_8px_rgba(0,255,135,0.2)]" :
              p.value === 'B' ? "bg-electric-blue/10 text-electric-blue border-electric-blue/30" :
              "bg-white/5 text-muted border-white/10"
            )}>
              {p.value}
            </span>
          </div>
        )
      },
      {
        headerName: "MOAT",
        valueGetter: (p) => p.data?.fundamentals.moat,
        width: 110,
        cellRenderer: (p: any) => (
          <div className="flex items-center justify-center h-full">
             <span className={clsx(
              "font-mono font-black text-xs",
              p.value === 'Wide' ? "text-neon-green" : p.value === 'Narrow' ? "text-electric-blue" : "text-muted"
            )}>
              {p.value}
            </span>
          </div>
        )
      },
      {
        headerName: "SCORE",
        valueGetter: (p) => p.data?.alpha_score.total,
        width: 100,
        valueFormatter: (p: ValueFormatterParams) => Number(p.value ?? 0).toFixed(0),
        cellStyle: (p) => ({ 
          color: (p.value as number) >= 70 ? "#10B981" : "#F8FAFC",
          fontFamily: "'JetBrains Mono'",
          fontWeight: "800",
          textAlign: "center"
        } as any),
      },
      {
        headerName: "MKT SHARE",
        valueGetter: (p) => p.data?.fundamentals.market_share_pct,
        width: 100,
        valueFormatter: (p: ValueFormatterParams) => fmtPct(p.value as number, false),
        cellStyle: { color: "#E8EBF0", fontFamily: "'JetBrains Mono'" } as any,
      },
      {
        headerName: "MKT CAP",
        valueGetter: (p) => p.data?.fundamentals.market_cap,
        width: 110,
        valueFormatter: (p: ValueFormatterParams) => fmtCap(p.value as number),
        cellStyle: { color: "#94A3B8", fontFamily: "'JetBrains Mono'", fontSize: "11px" } as any,
      },
      {
        headerName: "REV GROWTH",
        valueGetter: (p) => p.data?.fundamentals.revenue_growth_yoy,
        width: 130,
        valueFormatter: (p: ValueFormatterParams) => fmtPct(p.value as number, true),
        cellStyle: { color: "#10B981", fontFamily: "'JetBrains Mono'", fontWeight: "600" } as any,
      },
      {
        headerName: "FCF YIELD",
        valueGetter: (p) => p.data?.fundamentals.fcf_yield,
        width: 110,
        valueFormatter: (p: ValueFormatterParams) => fmtPct(p.value as number, true),
        cellStyle: { color: "#3B82F6", fontFamily: "'JetBrains Mono'", fontWeight: "600" } as any,
      },
    ],
    []
  );

  const getRowStyle = (params: RowClassParams<TickerValidation>) => {
    if (params.data?.recommendation === "STRONG_BUY") {
      return { borderLeft: "4px solid #10B981", background: "rgba(16, 185, 129, 0.05)" };
    }
    return undefined;
  };

  return (
    <div className="glass-panel p-0 overflow-hidden relative">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 w-64 h-32 bg-neon-green/5 blur-[60px] pointer-events-none" />

      
      <div className="p-5 border-b border-white/5 flex items-center justify-between bg-black/20 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-neon-green/10 border border-neon-green/20">
            <Gem className="w-4 h-4 text-neon-green" />
          </div>
          <div>
            <span className="card-header border-none pl-0 mb-0">Hidden Gems Screener 6.0</span>
            <p className="text-[10px] text-muted font-mono mt-1 tracking-widest uppercase">Institutional Quality Growth Signals</p>
          </div>
        </div>
        
        <div className="flex gap-4">
          <div className="flex flex-col items-end">
            <span className="text-[10px] font-mono text-muted">Signals</span>
            <span className="text-sm font-mono font-black text-neon-green">{rows.length}</span>
          </div>
        </div>
      </div>

      <div className="ag-theme-alpine-dark w-full" style={{ height: 500 }}>
        <AgGridReact<TickerValidation>
          rowData={rows}
          columnDefs={columnDefs}
          defaultColDef={{
            resizable: true,
            sortable: true,
            filter: false,
            suppressMovable: true,
          }}
          rowHeight={48}
          headerHeight={44}
          animateRows
          getRowStyle={getRowStyle}
          overlayNoRowsTemplate={
            isLoading 
              ? '<div class="font-mono text-xs text-electric-blue animate-pulse">Scanning universe for hidden alpha...</div>'
              : '<div class="font-mono text-xs text-muted">No institutional gems detected in this cycle.</div>'
          }
        />
      </div>
      
      <div className="p-4 bg-black/40 border-t border-white/5 flex items-center justify-between text-[9px] font-mono text-muted tracking-widest uppercase font-bold">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5">
             <Layers className="w-3 h-3" />
             <span>Scan: S&P 500 + Russell 2000</span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Activity className="w-3 h-3 text-neon-green animate-pulse" />
          <span>Engine Status: Nominal</span>
        </div>
      </div>
    </div>
  );
}
