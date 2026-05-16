"use client";

import { Suspense } from "react";
import { motion } from "framer-motion";
import TickerValidator from "@/components/TickerValidator";
import AlphaBubbleChart from "@/components/charts/AlphaBubbleChart";
import { Target, Search } from "lucide-react";

export default function ValidatorPage() {
  return (
    <div className="min-h-screen bg-[#0B0E14] px-6 pb-20 pt-10">

      <div className="max-w-screen-2xl mx-auto">
        <header className="pt-6 pb-10 border-b border-white/5 mb-8">
           <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-electric-blue/10 border border-electric-blue/20">
                <Search className="w-5 h-5 text-electric-blue" />
              </div>
              <h1 className="text-3xl font-mono font-black tracking-tighter text-white">
                INSTITUTIONAL <span className="text-electric-blue">VALIDATOR</span>
              </h1>
            </div>
            <p className="text-muted text-xs font-mono font-bold mt-2 tracking-widest uppercase">
              Real-time Quantitative Analysis & Confluence Scoring
            </p>
        </header>

        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8 items-start">
          <motion.div 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="xl:col-span-4"
          >
            <Suspense fallback={<LoadingCard title="TICKER VALIDATOR" />}>
              <TickerValidator />
            </Suspense>
          </motion.div>

          <motion.div 
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="xl:col-span-8"
          >
            <Suspense fallback={<LoadingCard title="BUBBLE MATRIX" />}>
              <div className="card p-6 min-h-[500px]">
                <div className="card-header border-neon-green text-neon-green">Sector Positioning Matrix</div>
                <AlphaBubbleChart />
              </div>
            </Suspense>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function LoadingCard({ title }: { title: string }) {
  return (
    <div className="card p-10 animate-pulse bg-white/5">
      <div className="h-4 bg-white/5 rounded w-1/4 mb-6" />
      <div className="h-96 bg-white/5 rounded-2xl" />
    </div>
  );
}
