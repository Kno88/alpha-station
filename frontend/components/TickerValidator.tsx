"use client";

import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, Download, Loader2, TrendingUp, Activity, Zap,
  Target, ShieldAlert, ShieldCheck, BarChart2, Heart, Shield,
  CheckCircle2, XCircle, ChevronDown, ChevronUp,
} from "lucide-react";
import clsx from "clsx";
import {
  Chart as ChartJS, RadialLinearScale, PointElement,
  LineElement, Filler, Tooltip, Legend,
} from "chart.js";
import { Radar } from "react-chartjs-2";
import { api, TickerValidation, fmtPct, fmtCap } from "@/lib/api";

ChartJS.register(RadialLinearScale, PointElement, LineElement, Filler, Tooltip, Legend);

// ── Radar Chart ───────────────────────────────────────────────────────────────
function QVMRadarChart({ data }: { data: TickerValidation }) {
  const g = (data.alpha_score.growth_score / 30) * 100;
  const p = (data.alpha_score.profitability_score / 30) * 100;
  const m = (data.alpha_score.moat_score / 20) * 100;
  const h = (data.alpha_score.health_score / 20) * 100;

  return (
    <Radar
      data={{
        labels: ["GROWTH", "PROFIT", "MOAT", "HEALTH"],
        datasets: [{
          label: "Profile",
          data: [g, p, m, h],
          backgroundColor: "rgba(0,255,135,0.12)",
          borderColor: "#00FF87",
          borderWidth: 2,
          pointBackgroundColor: "#00FF87",
          pointBorderColor: "#fff",
        }],
      }}
      options={{
        scales: {
          r: {
            angleLines: { color: "rgba(255,255,255,0.08)" },
            grid: { color: "rgba(255,255,255,0.08)" },
            pointLabels: { color: "#A0AECB", font: { size: 9, family: "'JetBrains Mono'", weight: "bold" as const } },
            ticks: { display: false, stepSize: 25 },
            suggestedMin: 0, suggestedMax: 100,
          },
        },
        plugins: { legend: { display: false } },
      }}
    />
  );
}

// ── Score Badge ───────────────────────────────────────────────────────────────
function ScoreBadge({ score, grade }: { score: number; grade: string }) {
  const color = score >= 75 ? "#10B981" : score >= 60 ? "#3B82F6" : score >= 40 ? "#F59E0B" : "#EF4444";
  return (
    <div className="flex flex-col items-center justify-center p-5 rounded-2xl glass-panel min-w-[110px]">
      <span className="text-[9px] font-mono font-bold text-muted tracking-widest uppercase mb-1">Alpha Score</span>
      <div className="text-4xl font-mono font-black" style={{ color, textShadow: `0 0 20px ${color}60` }}>
        {score.toFixed(0)}
      </div>
      <div className="px-3 py-1 mt-2 rounded-full bg-white/5 border border-white/10 text-[10px] font-mono font-black text-white tracking-widest">
        GRADE {grade}
      </div>
    </div>
  );
}

// ── Rank Bar ──────────────────────────────────────────────────────────────────
function RankBar({ label, score, color = "neon-green" }: { label: string; score: number; color?: string }) {
  const safe = Math.min(100, Math.max(0, isNaN(score) ? 0 : score));
  const cls = color === "neon-green" ? "bg-neon-green shadow-[0_0_8px_#10B981]" : "bg-electric-blue shadow-[0_0_8px_#3B82F6]";
  const txt = color === "neon-green" ? "text-neon-green" : "text-electric-blue";
  return (
    <div className="p-3 rounded-xl glass-panel">
      <div className="flex justify-between items-center mb-1.5">
        <span className="text-[9px] font-mono font-black tracking-widest text-muted">{label}</span>
        <span className={clsx("text-xs font-mono font-black", txt)}>{safe.toFixed(0)}</span>
      </div>
      <div className="h-1.5 bg-black/50 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${safe}%` }}
          transition={{ duration: 1, type: "spring", stiffness: 50 }}
          className={clsx("h-full rounded-full", cls)}
        />
      </div>
    </div>
  );
}

// ── Metric Chip (inspirado en Koyfin / Finviz) ────────────────────────────────
function MetricChip({
  label, value, status,
}: { label: string; value: string; status: "good" | "warn" | "bad" | "neutral" }) {
  const colors = {
    good: "border-neon-green/25 bg-neon-green/5 text-neon-green",
    warn: "border-amber-400/25 bg-amber-400/5 text-amber-400",
    bad:  "border-danger/25 bg-danger/5 text-danger",
    neutral: "border-white/10 bg-white/[0.03] text-text-secondary",
  };
  return (
    <div className={clsx("rounded-xl border px-3.5 py-3 flex flex-col gap-1", colors[status])}>
      <span className="text-[9px] font-mono font-bold text-muted uppercase tracking-widest">{label}</span>
      <span className="text-sm font-mono font-black">{value}</span>
    </div>
  );
}

// ── Confluence Checklist ───────────────────────────────────────────────────────
function ConfluenceChecklist({ data }: { data: TickerValidation }) {
  const [open, setOpen] = useState(false);
  const passed = data.confluence_checklist.filter((c) => c.passed).length;
  const total = data.confluence_checklist.length;
  return (
    <div className="rounded-xl glass-panel overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-electric-blue" />
          <span className="text-[10px] font-mono font-black tracking-widest text-white uppercase">
            Confluence Checklist
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-[10px] font-mono text-muted">{passed}/{total} passed</span>
          {open ? <ChevronUp className="w-3.5 h-3.5 text-muted" /> : <ChevronDown className="w-3.5 h-3.5 text-muted" />}
        </div>
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-white/5"
          >
            <div className="p-4 space-y-2">
              {data.confluence_checklist.map((item, i) => (
                <div key={i} className="flex items-center justify-between py-1.5">
                  <div className="flex items-center gap-2">
                    {item.passed
                      ? <CheckCircle2 className="w-3.5 h-3.5 text-neon-green shrink-0" />
                      : <XCircle className="w-3.5 h-3.5 text-danger/60 shrink-0" />}
                    <span className={clsx("text-[10px] font-mono", item.passed ? "text-text-secondary" : "text-muted/60")}>
                      {item.name}
                    </span>
                  </div>
                  <span className={clsx("text-[10px] font-mono font-bold", item.passed ? "text-neon-green" : "text-muted/50")}>
                    {item.value ?? "—"}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Intelligence Report (Simply Wall St style — data-driven) ──────────────────
function IntelligenceReport({ data }: { data: TickerValidation }) {
  const f = data.fundamentals;
  const s = data.alpha_score;
  const rec = data.recommendation;

  // Identify top strengths from checklist
  const strengths = data.confluence_checklist.filter((c) => c.passed);
  const weaknesses = data.confluence_checklist.filter((c) => !c.passed);

  // Build data-driven thesis
  const buildThesis = () => {
    const parts: string[] = [];

    // Valuation context
    if (f.pe_ratio && f.pe_ratio > 0) {
      parts.push(f.pe_ratio < 20
        ? `con un P/E de ${f.pe_ratio.toFixed(1)}x que sugiere valoración razonable`
        : `cotizando a ${f.pe_ratio.toFixed(1)}x beneficios (prima de crecimiento)`);
    }

    // Revenue narrative
    if (f.revenue_growth_yoy) {
      const pct = (f.revenue_growth_yoy * 100).toFixed(1);
      parts.push(f.revenue_growth_yoy >= 0.20
        ? `crecimiento de ingresos elite del +${pct}% YoY`
        : f.revenue_growth_yoy > 0
        ? `ingresos creciendo +${pct}% YoY`
        : `ingresos contrayéndose ${pct}% YoY`);
    }

    // Margin quality
    if (f.net_margin) {
      const pct = (f.net_margin * 100).toFixed(1);
      parts.push(f.net_margin >= 0.10
        ? `márgenes netos sólidos del ${pct}%`
        : f.net_margin > 0
        ? `márgenes netos ajustados del ${pct}%`
        : `márgenes negativos (${pct}%)`);
    }

    // Moat
    if (f.moat === "Wide") parts.push("foso económico WIDE con ventajas duraderas");
    else if (f.moat === "Narrow") parts.push("foso económico NARROW en desarrollo");

    return parts.length > 0
      ? `${f.company_name} presenta ${parts.join(", ")}.`
      : `${f.company_name} tiene un perfil fundamental con Alpha Score de ${s.total.toFixed(0)}/100.`;
  };

  const recColors: Record<string, string> = {
    STRONG_BUY: "text-neon-green border-neon-green/30 bg-neon-green/10",
    BUY: "text-electric-blue border-electric-blue/30 bg-electric-blue/10",
    HOLD: "text-amber-400 border-amber-400/30 bg-amber-400/10",
    AVOID: "text-danger border-danger/30 bg-danger/10",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl bg-black/40 border border-white/[0.06] overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 border-b border-white/[0.05] bg-gradient-to-r from-white/[0.04] to-transparent flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-electric-blue" />
          <span className="text-[10px] font-mono font-black tracking-[0.2em] text-white">
            INSTITUTIONAL INTELLIGENCE REPORT
          </span>
        </div>
        <div className={clsx("px-3 py-1 rounded-full border text-[10px] font-mono font-black tracking-widest", recColors[rec] ?? "text-muted border-white/10 bg-white/5")}>
          {rec.replace("_", " ")}
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Executive Summary */}
        <div>
          <div className="text-[9px] font-mono font-bold text-electric-blue mb-2 uppercase tracking-[0.15em]">
            ▸ Executive Summary
          </div>
          <p className="text-[11px] text-text-secondary leading-relaxed">{buildThesis()}</p>
        </div>

        {/* Strengths */}
        {strengths.length > 0 && (
          <div>
            <div className="text-[9px] font-mono font-bold text-neon-green mb-2 uppercase tracking-[0.15em] flex items-center gap-1.5">
              <Zap className="w-3 h-3" />
              Puntos Fuertes ({strengths.length})
            </div>
            <div className="space-y-1.5">
              {strengths.map((s, i) => (
                <div key={i} className="flex items-center justify-between text-[10px] font-mono">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-3 h-3 text-neon-green shrink-0" />
                    <span className="text-text-secondary">{s.name}</span>
                  </div>
                  <span className="text-neon-green font-bold ml-4 shrink-0">{s.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Weaknesses */}
        {weaknesses.length > 0 && (
          <div>
            <div className="text-[9px] font-mono font-bold text-danger mb-2 uppercase tracking-[0.15em] flex items-center gap-1.5">
              <ShieldAlert className="w-3 h-3" />
              Riesgos & Debilidades ({weaknesses.length})
            </div>
            <div className="space-y-1.5">
              {weaknesses.slice(0, 4).map((w, i) => (
                <div key={i} className="flex items-center justify-between text-[10px] font-mono">
                  <div className="flex items-center gap-2">
                    <XCircle className="w-3 h-3 text-danger/60 shrink-0" />
                    <span className="text-muted/70">{w.name}</span>
                  </div>
                  <span className="text-danger/70 font-bold ml-4 shrink-0">{w.value ?? "N/A"}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Key Ratios Grid (Koyfin-inspired) */}
        <div>
          <div className="text-[9px] font-mono font-bold text-muted mb-2 uppercase tracking-[0.15em]">
            ▸ Métricas Clave
          </div>
          <div className="grid grid-cols-2 gap-2">
            <MetricChip
              label="P/E Ratio"
              value={f.pe_ratio ? `${f.pe_ratio.toFixed(1)}x` : "—"}
              status={f.pe_ratio ? (f.pe_ratio < 20 ? "good" : f.pe_ratio < 40 ? "warn" : "bad") : "neutral"}
            />
            <MetricChip
              label="P/S Ratio"
              value={f.ps_ratio ? `${f.ps_ratio.toFixed(1)}x` : "—"}
              status={f.ps_ratio ? (f.ps_ratio < 3 ? "good" : f.ps_ratio < 8 ? "warn" : "bad") : "neutral"}
            />
            <MetricChip
              label="Gross Margin"
              value={fmtPct(f.gross_margin, true)}
              status={f.gross_margin ? (f.gross_margin > 0.5 ? "good" : f.gross_margin > 0.3 ? "warn" : "bad") : "neutral"}
            />
            <MetricChip
              label="ROE"
              value={fmtPct(f.roe, true)}
              status={f.roe ? (f.roe > 0.15 ? "good" : f.roe > 0 ? "warn" : "bad") : "neutral"}
            />
            <MetricChip
              label="Debt/Equity"
              value={f.debt_to_equity ? `${f.debt_to_equity.toFixed(2)}x` : "—"}
              status={f.debt_to_equity ? (f.debt_to_equity < 1 ? "good" : f.debt_to_equity < 2 ? "warn" : "bad") : "neutral"}
            />
            <MetricChip
              label="Piotroski"
              value={f.piotroski_f_score ? `${f.piotroski_f_score.toFixed(0)}/9` : "—"}
              status={f.piotroski_f_score ? (f.piotroski_f_score >= 7 ? "good" : f.piotroski_f_score >= 4 ? "warn" : "bad") : "neutral"}
            />
            <MetricChip
              label="FCF Yield"
              value={fmtPct(f.fcf_yield, true)}
              status={f.fcf_yield ? (f.fcf_yield > 0.05 ? "good" : f.fcf_yield > 0 ? "warn" : "bad") : "neutral"}
            />
            <MetricChip
              label="Mkt Cap"
              value={fmtCap(f.market_cap)}
              status="neutral"
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-5 py-3 bg-white/[0.02] border-t border-white/[0.05] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="w-3 h-3 text-muted" />
          <span className="text-[8px] font-mono text-muted uppercase tracking-widest">
            Quality Rank: {data.alpha_score.quality_rank} · Value Rank: {data.alpha_score.value_rank}
          </span>
        </div>
        <span className="text-[8px] font-mono text-muted">REF: AS-6-{data.ticker}</span>
      </div>
    </motion.div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export default function TickerValidator() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<TickerValidation | null>(null);
  const [error, setError] = useState<string | null>(null);

  const validate = useCallback(async (ticker: string) => {
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      setData(await api.validate(ticker.trim().toUpperCase()));
    } catch (e: any) {
      setError(e.message || "Validation failed");
    } finally {
      setLoading(false);
    }
  }, []);

  return (
    <div className="glass-panel p-6 flex flex-col gap-5 relative overflow-hidden">
      <div className="absolute -top-32 -right-32 w-64 h-64 bg-electric-blue/8 rounded-full blur-[100px] pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between relative z-10">
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-electric-blue drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
          <span className="card-header border-none pl-0 mb-0">Ticker Validator Pro 6.0</span>
        </div>
        {data && (
          <motion.button
            whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}
            onClick={() => window.open(api.reportUrl(data.ticker), "_blank")}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-white text-[10px] font-mono font-bold hover:bg-white/10 transition-all"
          >
            <Download className="w-3 h-3" />
            PDF
          </motion.button>
        )}
      </div>

      {/* Search */}
      <form onSubmit={(e) => { e.preventDefault(); validate(query); }} className="relative z-10">
        <div className="flex items-center gap-2">
          <div className="relative flex-1 group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-muted group-focus-within:text-electric-blue transition-colors pointer-events-none" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value.toUpperCase())}
              placeholder="TICKER (NVDA, AAPL...)"
              className="w-full bg-black/40 backdrop-blur-md border border-white/10 rounded-xl pl-11 pr-4 py-4 text-sm font-mono text-white placeholder:text-muted focus:outline-none focus:border-electric-blue/50 focus:ring-1 focus:ring-electric-blue/30 transition-all"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="shrink-0 px-4 py-4 rounded-xl btn-primary flex items-center gap-2 text-xs"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "ANALYZE"}
          </button>
        </div>
      </form>

      {/* Quick Picks */}
      <div className="flex flex-wrap gap-2 relative z-10">
        {["NVDA", "AAPL", "MSFT", "AXON", "MNDY"].map((t) => (
          <button
            key={t}
            onClick={() => { setQuery(t); validate(t); }}
            className="px-3 py-1 rounded-lg bg-white/5 border border-white/5 text-muted text-[10px] font-mono font-bold hover:border-white/20 hover:text-white transition-all"
          >
            {t}
          </button>
        ))}
      </div>

      {/* Error */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }}
            className="rounded-xl border border-danger/30 bg-danger/10 p-4 text-[11px] text-danger font-mono flex items-center gap-2"
          >
            <ShieldAlert className="w-4 h-4" />
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading */}
      {loading && (
        <div className="space-y-3 animate-pulse relative z-10">
          <div className="h-28 bg-white/5 rounded-2xl" />
          <div className="grid grid-cols-2 gap-2">
            {[...Array(4)].map((_, i) => <div key={i} className="h-16 bg-white/5 rounded-xl" />)}
          </div>
        </div>
      )}

      {/* Results */}
      <AnimatePresence>
        {data && !loading && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            className="space-y-5 relative z-10"
          >
            {/* Company Header */}
            <div className="flex items-center gap-4 p-4 rounded-2xl glass-panel">
              <ScoreBadge score={data.alpha_score.total} grade={data.alpha_score.grade} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-1">
                  <span className="text-3xl font-mono font-black text-white tracking-tighter">{data.ticker}</span>
                  <span className={clsx(
                    "px-2.5 py-0.5 rounded-full border text-[9px] font-mono font-black",
                    data.fundamentals.moat === "Wide" ? "bg-neon-green/10 border-neon-green/20 text-neon-green" :
                    data.fundamentals.moat === "Narrow" ? "bg-electric-blue/10 border-electric-blue/20 text-electric-blue" :
                    "bg-white/5 border-white/10 text-muted"
                  )}>
                    MOAT: {data.fundamentals.moat?.toUpperCase() || "NONE"}
                  </span>
                </div>
                <p className="text-xs font-bold text-text-secondary truncate">{data.fundamentals.company_name}</p>
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[9px] font-mono text-muted uppercase tracking-widest">
                    {data.fundamentals.sector || "Unknown"}
                  </span>
                  <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[9px] font-mono text-muted">
                    {fmtCap(data.fundamentals.market_cap)}
                  </span>
                  <span className="px-2 py-0.5 rounded-md bg-white/5 border border-white/10 text-[9px] font-mono text-muted">
                    MKT SHARE: {data.fundamentals.market_share_pct?.toFixed(1) ?? "—"}%
                  </span>
                </div>
              </div>
            </div>

            {/* Radar + Rank Bars */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="glass-panel p-4 flex flex-col items-center">
                <span className="text-[10px] font-mono font-bold text-muted tracking-widest uppercase mb-3 w-full border-l-2 border-neon-green pl-2 flex items-center gap-2">
                  <Activity className="w-3 h-3 text-neon-green" />
                  Fundamental Profile
                </span>
                <div className="h-44 w-full">
                  <QVMRadarChart data={data} />
                </div>
              </div>
              <div className="flex flex-col gap-2">
                <RankBar label="GROWTH" score={(data.alpha_score.growth_score / 30) * 100} />
                <RankBar label="PROFITABILITY" score={(data.alpha_score.profitability_score / 30) * 100} />
                <RankBar label="MOAT" score={(data.alpha_score.moat_score / 20) * 100} color="electric-blue" />
                <RankBar label="HEALTH" score={(data.alpha_score.health_score / 20) * 100} color="electric-blue" />
              </div>
            </div>

            {/* Confluence Checklist */}
            <ConfluenceChecklist data={data} />

            {/* Intelligence Report */}
            <IntelligenceReport data={data} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
