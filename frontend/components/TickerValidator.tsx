"use client";

import { useState, useCallback, useRef } from "react";
import { toast } from "react-toastify";
import {
  Search,
  Download,
  Loader2,
  CheckCircle2,
  XCircle,
  TrendingUp,
  Activity,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import clsx from "clsx";
import {
  api,
  TickerValidation,
  ConfluenceItem,
  fmtPct,
  fmtCap,
  fmtGex,
  stageColor,
  recColor,
} from "@/lib/api";

// ── Alpha Score Ring ──────────────────────────────────────────────────────────
function ScoreRing({ score, grade }: { score: number; grade: string }) {
  const r = 38;
  const circ = 2 * Math.PI * r;
  const filled = (score / 100) * circ;
  const color =
    score >= 70 ? "#00FF87" : score >= 50 ? "#0088FF" : "#FF4560";

  return (
    <div className="relative flex items-center justify-center w-24 h-24">
      <svg width="96" height="96" className="-rotate-90">
        <circle cx="48" cy="48" r={r} stroke="#2D3A52" strokeWidth="6" fill="none" />
        <circle
          cx="48"
          cy="48"
          r={r}
          stroke={color}
          strokeWidth="6"
          fill="none"
          strokeDasharray={`${filled} ${circ}`}
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 6px ${color})`, transition: "stroke-dasharray 0.8s ease" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="font-mono font-bold text-xl" style={{ color }}>
          {score.toFixed(0)}
        </span>
        <span className="font-mono text-xs text-muted">{grade}</span>
      </div>
    </div>
  );
}

// ── Confluence Row ────────────────────────────────────────────────────────────
function ConfluenceRow({ item }: { item: ConfluenceItem }) {
  return (
    <div className="flex items-start gap-2 py-1.5 border-b border-border/40 last:border-0">
      <span className="mt-0.5 flex-shrink-0">
        {item.passed ? (
          <CheckCircle2 className="w-3.5 h-3.5 text-neon-green" />
        ) : (
          <XCircle className="w-3.5 h-3.5 text-danger/60" />
        )}
      </span>
      <span className={clsx("text-xs flex-1", item.passed ? "text-text-secondary" : "text-muted")}>
        {item.name}
      </span>
      {item.value && (
        <span
          className={clsx(
            "text-xs font-mono flex-shrink-0",
            item.passed ? "text-neon-green" : "text-muted"
          )}
        >
          {item.value}
        </span>
      )}
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function TickerValidator() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<TickerValidation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validate = useCallback(async (ticker: string) => {
    if (!ticker.trim()) return;
    setLoading(true);
    setError(null);
    setData(null);
    setShowAll(false);

    try {
      const result = await api.validate(ticker.trim().toUpperCase());
      setData(result);

      if (result.stage.stage === "Stage 2" && result.liquidity.rvol >= 2.5) {
        toast.success(
          `🚀 ${ticker.toUpperCase()} — Stage 2 breakout! RVOL ${result.liquidity.rvol.toFixed(1)}x`,
          { autoClose: 7000 }
        );
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Validation failed";
      setError(msg);
      toast.error(`${ticker.toUpperCase()}: ${msg}`);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    validate(query);
  };

  const handlePdfDownload = async () => {
    if (!data) return;
    setPdfLoading(true);
    try {
      const url = api.reportUrl(data.ticker);
      const res = await fetch(url);
      if (!res.ok) throw new Error("PDF generation failed");
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `alpha_report_${data.ticker}.pdf`;
      link.click();
      toast.success(`Report downloaded: ${data.ticker}.pdf`);
    } catch {
      toast.error("PDF download failed");
    } finally {
      setPdfLoading(false);
    }
  };

  const visibleChecklist = showAll
    ? (data?.confluence_checklist ?? [])
    : (data?.confluence_checklist ?? []).slice(0, 6);

  const passCount = data?.confluence_checklist.filter((c) => c.passed).length ?? 0;
  const totalCount = data?.confluence_checklist.length ?? 0;

  return (
    <div className="card p-5 flex flex-col gap-4">
      {/* ── Header ────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between">
        <span className="card-header">◈ TICKER VALIDATOR PRO</span>
        {data && (
          <button
            onClick={handlePdfDownload}
            disabled={pdfLoading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-electric-blue/10 border border-electric-blue/20 text-electric-blue text-xs font-mono hover:bg-electric-blue/20 transition-all disabled:opacity-50"
          >
            {pdfLoading ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Download className="w-3.5 h-3.5" />
            )}
            PDF
          </button>
        )}
      </div>

      {/* ── Search bar ────────────────────────────────────────────────────── */}
      <form onSubmit={handleSubmit} className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value.toUpperCase())}
          placeholder="Enter ticker (e.g. NVDA, SMCI)"
          className="w-full bg-oxford border border-border rounded-lg pl-9 pr-20 py-2.5 text-sm font-mono text-text-primary placeholder:text-muted focus:outline-none focus:border-electric-blue focus:ring-1 focus:ring-electric-blue/30 transition-all"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1 rounded-md bg-electric-blue text-white text-xs font-mono font-semibold disabled:opacity-40 hover:bg-electric-blue/90 transition-all flex items-center gap-1"
        >
          {loading ? <Loader2 className="w-3 h-3 animate-spin" /> : "VALIDATE"}
        </button>
      </form>

      {/* ── Quick picks ───────────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-1.5">
        {["NVDA", "SMCI", "AXON", "CELH", "ASTS", "IONQ", "DUOL", "MNDY"].map((t) => (
          <button
            key={t}
            onClick={() => { setQuery(t); validate(t); }}
            className="px-2 py-0.5 rounded bg-oxford border border-border text-muted text-xs font-mono hover:border-electric-blue/40 hover:text-electric-blue transition-all"
          >
            {t}
          </button>
        ))}
      </div>

      {/* ── Error state ───────────────────────────────────────────────────── */}
      {error && (
        <div className="rounded-lg border border-danger/30 bg-danger/5 p-3 text-xs text-danger font-mono">
          ✗ {error}
        </div>
      )}

      {/* ── Loading skeleton ──────────────────────────────────────────────── */}
      {loading && (
        <div className="space-y-3 animate-pulse">
          <div className="h-20 bg-border/30 rounded-xl" />
          <div className="h-4 bg-border/30 rounded w-3/4" />
          <div className="h-4 bg-border/30 rounded w-1/2" />
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-3 bg-border/20 rounded" />
            ))}
          </div>
        </div>
      )}

      {/* ── Results ───────────────────────────────────────────────────────── */}
      {data && !loading && (
        <div className="animate-fade-in space-y-4">
          {/* Score + company banner */}
          <div className="flex items-center gap-4 p-4 rounded-xl bg-oxford border border-border">
            <ScoreRing score={data.alpha_score.total} grade={data.alpha_score.grade} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xl font-mono font-bold text-neon-green text-glow-green">
                  {data.ticker}
                </span>
                <span
                  className="text-xs font-mono px-2 py-0.5 rounded border"
                  style={{
                    color: stageColor(data.stage.stage),
                    borderColor: stageColor(data.stage.stage) + "40",
                    background: stageColor(data.stage.stage) + "10",
                  }}
                >
                  {data.stage.stage}
                </span>
                <span
                  className="text-xs font-bold px-2.5 py-0.5 rounded-full border"
                  style={{
                    color: recColor(data.recommendation),
                    borderColor: recColor(data.recommendation) + "40",
                    background: recColor(data.recommendation) + "10",
                  }}
                >
                  {data.recommendation.replace("_", " ")}
                </span>
              </div>
              <p className="text-sm text-text-secondary mt-0.5 truncate">
                {data.fundamentals.company_name}
              </p>
              <p className="text-xs text-muted mt-0.5">
                {data.fundamentals.sector} · {data.fundamentals.industry}
              </p>
            </div>
          </div>

          {/* Key metrics grid */}
          <div className="grid grid-cols-2 gap-2">
            <MetricCard
              label="RVOL"
              value={`${data.liquidity.rvol.toFixed(2)}x`}
              highlight={data.liquidity.rvol >= 2.5}
              icon={<Activity className="w-3 h-3" />}
            />
            <MetricCard
              label="PRICE"
              value={`$${data.stage.price.toFixed(2)}`}
              sub={`vs MA200: ${data.stage.price_vs_ma200_pct > 0 ? "+" : ""}${data.stage.price_vs_ma200_pct.toFixed(1)}%`}
            />
            <MetricCard
              label="REV GROWTH"
              value={fmtPct(data.fundamentals.revenue_growth_yoy, true)}
              highlight={data.fundamentals.high_growth}
              icon={<TrendingUp className="w-3 h-3" />}
            />
            <MetricCard
              label="MKT CAP"
              value={fmtCap(data.fundamentals.market_cap)}
            />
          </div>

          {/* GEX summary */}
          {data.gex.available && (
            <div className="rounded-lg border border-border bg-oxford p-3">
              <div className="card-header mb-2">GEX SUMMARY</div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <div className="text-xs text-muted">Net GEX</div>
                  <div
                    className="font-mono text-sm font-semibold"
                    style={{ color: data.gex.gex_total >= 0 ? "#00FF87" : "#FF4560" }}
                  >
                    {fmtGex(data.gex.gex_total)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted">Flip Level</div>
                  <div className="font-mono text-sm text-amber">
                    {data.gex.gex_flip_level ? `$${data.gex.gex_flip_level}` : "—"}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted">P/C Ratio</div>
                  <div className="font-mono text-sm text-text-secondary">
                    {data.gex.put_call_ratio?.toFixed(2) ?? "—"}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Confluence checklist */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="card-header">CONFLUENCE CHECKLIST</span>
              <span
                className={clsx(
                  "text-xs font-mono px-2 py-0.5 rounded-full",
                  passCount / totalCount >= 0.6
                    ? "bg-neon-green/10 text-neon-green"
                    : passCount / totalCount >= 0.4
                    ? "bg-amber/10 text-amber"
                    : "bg-danger/10 text-danger"
                )}
              >
                {passCount}/{totalCount}
              </span>
            </div>
            <div className="space-y-0">
              {visibleChecklist.map((item, i) => (
                <ConfluenceRow key={i} item={item} />
              ))}
            </div>
            {totalCount > 6 && (
              <button
                onClick={() => setShowAll(!showAll)}
                className="flex items-center gap-1 mt-2 text-xs text-electric-blue font-mono hover:underline"
              >
                {showAll ? (
                  <>
                    <ChevronUp className="w-3 h-3" /> Show less
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-3 h-3" /> Show {totalCount - 6} more
                  </>
                )}
              </button>
            )}
          </div>

          {/* MA key levels */}
          <div className="rounded-lg border border-border bg-oxford p-3">
            <div className="card-header mb-2">KEY LEVELS</div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
              {[
                ["MA 50", data.stage.ma50],
                ["MA 150", data.stage.ma150],
                ["MA 200", data.stage.ma200],
                ...(data.key_levels
                  ? Object.entries(data.key_levels).map(([k, v]) => [
                      k.replace("_", " ").toUpperCase(),
                      v,
                    ])
                  : []),
              ]
                .filter(([, v]) => v && Number(v) > 0)
                .map(([label, val]) => (
                  <div key={String(label)} className="flex justify-between">
                    <span className="text-xs text-muted">{label}</span>
                    <span className="text-xs font-mono text-text-secondary">
                      ${Number(val).toFixed(2)}
                    </span>
                  </div>
                ))}
            </div>
          </div>

          {/* Stage notes */}
          {data.stage.notes.length > 0 && (
            <div className="space-y-1">
              {data.stage.notes.map((note, i) => (
                <p key={i} className="text-xs text-muted font-mono">
                  {note}
                </p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Sub-component ─────────────────────────────────────────────────────────────
function MetricCard({
  label,
  value,
  sub,
  highlight = false,
  icon,
}: {
  label: string;
  value: string;
  sub?: string;
  highlight?: boolean;
  icon?: React.ReactNode;
}) {
  return (
    <div
      className={clsx(
        "rounded-lg border p-3 transition-all",
        highlight
          ? "bg-neon-green/5 border-neon-green/20"
          : "bg-oxford border-border"
      )}
    >
      <div className="flex items-center gap-1 text-muted text-xs mb-1">
        {icon}
        {label}
      </div>
      <div
        className={clsx(
          "font-mono font-semibold text-base",
          highlight ? "text-neon-green" : "text-text-primary"
        )}
      >
        {value}
      </div>
      {sub && <div className="text-xs text-muted font-mono mt-0.5">{sub}</div>}
    </div>
  );
}
