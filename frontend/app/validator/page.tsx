"use client";

import { Suspense } from "react";
import TickerValidator from "@/components/TickerValidator";
import AlphaBubbleChart from "@/components/charts/AlphaBubbleChart";
import AlertBanner from "@/components/alerts/AlertBanner";

export default function ValidatorPage() {
  return (
    <div className="min-h-screen bg-oxford px-4 pb-12">
      <AlertBanner />

      <div className="max-w-screen-2xl mx-auto">
        <div className="pt-6 pb-4 border-b border-border">
          <h1 className="text-2xl font-bold text-text-primary font-mono">
            <span className="text-electric-blue">◈</span> TICKER VALIDATOR
          </h1>
          <p className="text-muted text-sm mt-0.5">
            Stage Analysis · GEX Intelligence · Alpha Score · Confluence Checklist
          </p>
        </div>

        <div className="mt-6 grid grid-cols-1 xl:grid-cols-3 gap-6">
          <div className="xl:col-span-1">
            <Suspense
              fallback={
                <div className="card p-6 animate-pulse">
                  <div className="h-4 bg-border rounded w-1/2 mb-4" />
                  <div className="h-64 bg-border rounded" />
                </div>
              }
            >
              <TickerValidator />
            </Suspense>
          </div>

          <div className="xl:col-span-2">
            <Suspense
              fallback={
                <div className="card p-6 animate-pulse">
                  <div className="h-4 bg-border rounded w-1/2 mb-4" />
                  <div className="h-64 bg-border rounded" />
                </div>
              }
            >
              <AlphaBubbleChart />
            </Suspense>
          </div>
        </div>
      </div>
    </div>
  );
}
