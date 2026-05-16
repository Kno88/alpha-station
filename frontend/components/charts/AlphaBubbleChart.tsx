"use client";

import { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  BubbleController,
  LinearScale,
  PointElement,
  Tooltip,
  Legend,
  Title,
  type ChartOptions,
  type TooltipItem,
} from "chart.js";
import { Bubble } from "react-chartjs-2";
import { api, BubbleDataPoint, fmtCap } from "@/lib/api";
import { Loader2, RefreshCw, Info } from "lucide-react";

ChartJS.register(BubbleController, LinearScale, PointElement, Tooltip, Legend, Title);

const UNIVERSE_PRESETS: Record<string, string> = {
  "Growth Leaders": "NVDA,AXON,CELH,DUOL,MNDY",
  "Hidden Gems":    "ASTS,IONQ,RKLB,ACHR,SMAR",
  "Mag7 + AI":      "NVDA,MSFT,META,PLTR,GOOGL",
};

function getColor(point: BubbleDataPoint): string {
  if (point.moat === "Wide") return "#00FF87";
  if (point.moat === "Narrow") return "#0088FF";
  return "#6B7A99";
}

export default function AlphaBubbleChart() {
  const [data, setData] = useState<BubbleDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [preset, setPreset] = useState("Growth Leaders");

  const fetchData = async (tickers?: string) => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.bubbleData(tickers);
      setData(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load bubble data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData(UNIVERSE_PRESETS[preset]);
  }, [preset]);

  // ── Chart.js dataset ──────────────────────────────────────────────────────
  const chartData = {
    datasets: [
      {
        label: "Alpha Universe",
        data: data.map((d) => ({
          x: d.revenue_growth,
          y: d.market_cap_billions,
          r: Math.max(6, (d.alpha_score / 100) * 25),
        })),
        backgroundColor: data.map((d) => `${getColor(d)}22`),
        borderColor: data.map((d) => getColor(d)),
        borderWidth: 2,
        hoverBorderWidth: 3,
        hoverBackgroundColor: data.map((d) => `${getColor(d)}44`),
      },
    ],
  };

  const options: ChartOptions<"bubble"> = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 600 },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "#242E42",
        borderColor: "#2D3A52",
        borderWidth: 1,
        titleColor: "#0088FF",
        bodyColor: "#E8EBF0",
        padding: 12,
        callbacks: {
          title: (items: TooltipItem<"bubble">[]) => {
            const idx = items[0]?.dataIndex;
            if (idx == null) return "";
            const d = data[idx];
            return `${d.ticker} — ${d.company_name}`;
          },
          label: (item: TooltipItem<"bubble">) => {
            const idx = item.dataIndex;
            const d = data[idx];
            return [
              `  Moat: ${d.moat}`,
              `  Alpha Score: ${d.alpha_score.toFixed(0)}/100`,
              `  Rev Growth: ${d.revenue_growth > 0 ? "+" : ""}${d.revenue_growth.toFixed(1)}%`,
              `  Market Cap: $${d.market_cap_billions.toFixed(1)}B`,
            ].filter(Boolean);
          },
        },
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: "Revenue Growth YoY (%)",
          color: "#6B7A99",
          font: { family: "'JetBrains Mono'", size: 11 },
        },
        grid: { color: "#2D3A52" },
        ticks: {
          color: "#6B7A99",
          font: { family: "'JetBrains Mono'", size: 10 },
          callback: (v) => `${Number(v) > 0 ? "+" : ""}${v}%`,
        },
        border: { color: "#2D3A52" },
      },
      y: {
        title: {
          display: true,
          text: "Market Cap ($ Billions)",
          color: "#6B7A99",
          font: { family: "'JetBrains Mono'", size: 11 },
        },
        grid: { color: "#2D3A52" },
        ticks: {
          color: "#6B7A99",
          font: { family: "'JetBrains Mono'", size: 10 },
          callback: (v) => `${v}B`,
        },
        border: { color: "#2D3A52" },
      },
    },
    onHover: (event, elements) => {
      if (event.native?.target) {
        (event.native.target as HTMLElement).style.cursor = elements.length > 0 ? "pointer" : "default";
      }
    },
  };

  return (
    <div className="card p-5 flex flex-col gap-4 h-full">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div>
          <span className="card-header">◈ ALPHA BUBBLE CHART</span>
          <p className="text-xs text-muted mt-0.5">
            X: Revenue Growth · Y: Market Cap · Size: Alpha Score
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Preset selector */}
          <div className="flex gap-1">
            {Object.keys(UNIVERSE_PRESETS).map((p) => (
              <button
                key={p}
                onClick={() => setPreset(p)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition-all ${
                  preset === p
                    ? "bg-electric-blue/15 text-electric-blue border border-electric-blue/30"
                    : "text-muted border border-border hover:border-electric-blue/20 hover:text-text-secondary"
                }`}
              >
                {p}
              </button>
            ))}
          </div>
          <button
            onClick={() => fetchData(UNIVERSE_PRESETS[preset])}
            disabled={loading}
            className="p-1.5 rounded border border-border text-muted hover:text-electric-blue hover:border-electric-blue/30 transition-all disabled:opacity-40"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* ── Legend ──────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap gap-3 text-xs font-mono">
        {[
          { color: "#00FF87", label: "Wide Moat" },
          { color: "#0088FF", label: "Narrow Moat" },
          { color: "#6B7A99", label: "No Moat" },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <span
              className="w-3 h-3 rounded-full border-2"
              style={{ borderColor: color, background: color + "22" }}
            />
            <span className="text-muted">{label}</span>
          </div>
        ))}
        <div className="flex items-center gap-1 text-muted ml-auto">
          <Info className="w-3 h-3" />
          <span>Bubble size = Alpha Score</span>
        </div>
      </div>

      {/* ── Chart ───────────────────────────────────────────────────────── */}
      <div className="relative flex-1 min-h-[320px]">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-oxford/60 rounded-lg z-10">
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="w-6 h-6 text-electric-blue animate-spin" />
              <span className="text-xs text-muted font-mono">Fetching universe data...</span>
            </div>
          </div>
        )}
        {error && data.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-xs text-danger font-mono">{error}</p>
          </div>
        ) : data.length === 0 && !loading ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2">
            <span className="text-2xl opacity-20">📊</span>
            <p className="text-xs text-muted font-mono">No analysis data for this universe.</p>
          </div>
        ) : (
          <Bubble data={chartData} options={options} />
        )}
      </div>

      {/* ── Ticker labels ───────────────────────────────────────────────── */}
      {data.length > 0 && !loading && (
        <div className="flex flex-wrap gap-1.5">
          {data.map((d) => (
            <span
              key={d.ticker}
              className="text-xs font-mono px-1.5 py-0.5 rounded border transition-all"
              style={{
                color: getColor(d),
                borderColor: getColor(d) + "40",
                background: getColor(d) + "0A",
                boxShadow: d.moat === "Wide" ? `0 0 6px ${getColor(d)}40` : undefined,
              }}
            >
              {d.ticker}
              {d.moat === "Wide" && " 🏰"}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
