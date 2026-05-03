"use client";

import { Suspense } from "react";
import HiddenGemsTable from "@/components/HiddenGemsTable";
import AlertBanner from "@/components/alerts/AlertBanner";

export default function ScreenerPage() {
  return (
    <div className="min-h-screen bg-oxford px-4 pb-12">
      <AlertBanner />

      <div className="max-w-screen-2xl mx-auto">
        <div className="pt-6 pb-4 border-b border-border">
          <h1 className="text-2xl font-bold text-text-primary font-mono">
            <span className="text-neon-green">◈</span> HIDDEN GEMS SCREENER
          </h1>
          <p className="text-muted text-sm mt-0.5">
            Small/Mid Caps · Low Institutional Coverage · High Growth · Stage 2 Candidates
          </p>
        </div>

        <div className="mt-6">
          <Suspense
            fallback={
              <div className="card p-6 animate-pulse">
                <div className="h-4 bg-border rounded w-1/4 mb-4" />
                <div className="h-96 bg-border rounded" />
              </div>
            }
          >
            <HiddenGemsTable />
          </Suspense>
        </div>
      </div>
    </div>
  );
}
