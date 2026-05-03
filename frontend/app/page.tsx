"use client";

import { Suspense } from "react";
import TickerValidator from "@/components/TickerValidator";
import AlphaBubbleChart from "@/components/charts/AlphaBubbleChart";
import HiddenGemsTable from "@/components/HiddenGemsTable";
import AlertBanner from "@/components/alerts/AlertBanner";
import StatBar from "@/components/ui/StatBar";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-oxford px-4 pb-12">
      {/* ── Alert Banner ────────────────────────────────────────────────── */}
      <AlertBanner />

      {/* ── Page Header ─────────────────────────────────────────────────── */}
      <div className="max-w-screen-2xl mx-auto">
        <div className="pt-6 pb-4 border-b border-border flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text-primary font-mono">
              <span className="text-electric-blue">◈</span> ALPHA STATION{" "}
              <span className="text-neon-green text-glow-green">v4.0</span>
            </h1>
            <p className="text-muted text-sm mt-0.5">
              Exponential Growth Detection Engine · Stage Analysis · GEX Intelligence
            </p>
          </div>
          <StatBar />
        </div>

        {/* ── Main Grid ──────────────────────────────────────────────────── */}
        <div className="mt-6 grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Ticker Validator — full width on mobile, 1 col on xl */}
          <div className="xl:col-span-1">
            <Suspense fallback={<LoadingCard title="TICKER VALIDATOR" />}>
              <TickerValidator />
            </Suspense>
          </div>

          {/* Bubble Chart — 2 cols on xl */}
          <div className="xl:col-span-2">
            <Suspense fallback={<LoadingCard title="ALPHA BUBBLE CHART" />}>
              <AlphaBubbleChart />
            </Suspense>
          </div>
        </div>

        {/* ── Hidden Gems Table ───────────────────────────────────────────── */}
        <div className="mt-6">
          <Suspense fallback={<LoadingCard title="HIDDEN GEMS SCREENER" />}>
            <HiddenGemsTable />
          </Suspense>
        </div>
      </div>
    </div>
  );
}

function LoadingCard({ title }: { title: string }) {
  return (
    <div className="card p-6 animate-pulse">
      <div className="card-header mb-4">{title}</div>
      <div className="space-y-3">
        <div className="h-4 bg-border rounded w-3/4" />
        <div className="h-4 bg-border rounded w-1/2" />
        <div className="h-32 bg-border rounded" />
      </div>
    </div>
  );
}
