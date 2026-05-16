"use client";

import { Suspense, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import HiddenGemsTable from "@/components/HiddenGemsTable";
import AdvancedScreener from "@/components/AdvancedScreener";
import clsx from "clsx";
import { Layers, SlidersHorizontal, Activity } from "lucide-react";

export default function ScreenerPage() {
  const [activeTab, setActiveTab] = useState<"gems" | "advanced">("advanced");

  return (
    <div className="min-h-screen bg-[#0B0E14] px-6 pb-20 pt-10">

      <div className="max-w-screen-2xl mx-auto">
        <header className="pt-6 pb-10 border-b border-white/5 mb-8">
           <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-neon-green/10 border border-neon-green/20">
                <Activity className="w-5 h-5 text-neon-green" />
              </div>
              <h1 className="text-3xl font-mono font-black tracking-tighter text-white">
                ALPHA <span className="text-neon-green">SCREENER</span>
              </h1>
            </div>
            <p className="text-muted text-xs font-mono font-bold mt-2 tracking-widest uppercase">
              Professional Grade Discovery & Validation Engine
            </p>
        </header>

        {/* ── Tab navigation ──────────────────────────────────────────────── */}
        <div className="flex gap-4 mb-8">
          {[
            { id: "advanced", label: "ADVANCED FILTERS", icon: SlidersHorizontal },
            { id: "gems", label: "INSTITUTIONAL GEMS", icon: Layers },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={clsx(
                "relative flex items-center gap-2 px-6 py-3 rounded-xl text-[10px] font-black font-mono tracking-[0.2em] transition-all",
                activeTab === tab.id
                  ? "text-white glass bg-white/10"
                  : "text-muted hover:text-white hover:bg-white/5"
              )}
            >
              {activeTab === tab.id && (
                <motion.div
                  layoutId="screener-tab"
                  className="absolute inset-0 bg-neon-green/10 rounded-xl border border-neon-green/20"
                  transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                />
              )}
              <tab.icon className={clsx("w-3.5 h-3.5 relative z-10", activeTab === tab.id ? "text-neon-green" : "")} />
              <span className="relative z-10">{tab.label}</span>
            </button>
          ))}
        </div>

        <motion.div 
          key={activeTab}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
          className="mt-6"
        >
          {activeTab === "gems" && (
            <Suspense fallback={<LoadingSkeleton />}>
              <HiddenGemsTable />
            </Suspense>
          )}

          {activeTab === "advanced" && (
            <Suspense fallback={<LoadingSkeleton />}>
              <AdvancedScreener />
            </Suspense>
          )}
        </motion.div>
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="card p-10 animate-pulse bg-white/5">
      <div className="h-4 bg-white/5 rounded w-1/4 mb-6" />
      <div className="h-[600px] bg-white/5 rounded-2xl" />
    </div>
  );
}
