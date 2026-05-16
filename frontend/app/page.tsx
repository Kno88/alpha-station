"use client";

import { Suspense } from "react";
import { motion } from "framer-motion";
import TickerValidator from "@/components/TickerValidator";
import AlphaBubbleChart from "@/components/charts/AlphaBubbleChart";
import HiddenGemsTable from "@/components/HiddenGemsTable";
import StatBar from "@/components/ui/StatBar";
import { BarChart4, Cpu, ShieldCheck } from "lucide-react";

const containerVariants = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15
    }
  }
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-transparent px-6 pb-20 pt-6">

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="max-w-screen-2xl mx-auto"
      >
        {/* ── Page Header ─────────────────────────────────────────────────── */}
        <motion.div variants={itemVariants} className="pt-2 pb-8 flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-white/[0.05] mb-8 relative">
          {/* Subtle glow behind header */}
          <div className="absolute left-0 top-0 w-64 h-32 bg-electric-blue/10 blur-[100px] pointer-events-none" />
          
          <div className="space-y-4 relative z-10">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-electric-blue/10 border border-electric-blue/20 shadow-[0_0_15px_rgba(59,130,246,0.3)]">
                <BarChart4 className="w-6 h-6 text-electric-blue" />
              </div>
              <h1 className="text-4xl font-mono font-black tracking-tighter text-white">
                QUANTITATIVE <span className="text-transparent bg-clip-text bg-gradient-to-r from-electric-blue to-neon-green">TERMINAL</span>
              </h1>
            </div>
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 shadow-sm backdrop-blur-md">
                <Cpu className="w-3.5 h-3.5 text-muted" />
                <span className="text-[10px] font-mono font-bold text-muted tracking-widest uppercase">Engine: Alpha-v6.0</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-neon-green/5 border border-neon-green/20 shadow-[0_0_10px_rgba(16,185,129,0.1)] backdrop-blur-md">
                <ShieldCheck className="w-3.5 h-3.5 text-neon-green" />
                <span className="text-[10px] font-mono font-bold text-neon-green tracking-widest uppercase">Verified Institutional Model</span>
              </div>
            </div>
          </div>
          <div className="glass-panel p-4 rounded-2xl relative z-10">
            <StatBar />
          </div>
        </motion.div>

        {/* ── Main Grid ──────────────────────────────────────────────────── */}
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
          {/* Ticker Validator — 4 cols */}
          <motion.div variants={itemVariants} className="xl:col-span-4">
            <Suspense fallback={<LoadingCard title="TICKER VALIDATOR" />}>
              <TickerValidator />
            </Suspense>
          </motion.div>

          {/* Bubble Chart — 8 cols */}
          <motion.div variants={itemVariants} className="xl:col-span-8">
            <Suspense fallback={<LoadingCard title="ALPHA BUBBLE CHART" />}>
              <div className="card p-6 h-full min-h-[500px]">
                <div className="card-header">Institutional Bubble Matrix</div>
                <AlphaBubbleChart />
              </div>
            </Suspense>
          </motion.div>
        </div>

        {/* ── Hidden Gems Table ───────────────────────────────────────────── */}
        <motion.div variants={itemVariants} className="mt-8">
          <Suspense fallback={<LoadingCard title="HIDDEN GEMS SCREENER" />}>
            <HiddenGemsTable />
          </Suspense>
        </motion.div>
      </motion.div>
    </div>
  );
}

function LoadingCard({ title }: { title: string }) {
  return (
    <div className="card p-6 animate-pulse bg-white/5">
      <div className="card-header mb-4">{title}</div>
      <div className="space-y-4">
        <div className="h-4 bg-white/5 rounded w-3/4" />
        <div className="h-4 bg-white/5 rounded w-1/2" />
        <div className="h-48 bg-white/5 rounded-xl" />
      </div>
    </div>
  );
}
