"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, BookOpen, TrendingUp, Shield, Heart, Zap, Target, BarChart2, Info } from "lucide-react";

const SCORE_DIMS = [
  {
    label: "Growth Score",
    max: 30,
    icon: TrendingUp,
    color: "text-neon-green",
    border: "border-neon-green/20",
    bg: "bg-neon-green/5",
    items: [
      { metric: "Revenue Growth ≥ 20% YoY", pts: "+15 pts", note: "Core signal of compounding power" },
      { metric: "Revenue Growth 10–20% YoY", pts: "+8 pts", note: "Healthy but not elite" },
      { metric: "Earnings Growth ≥ 15% YoY", pts: "+15 pts", note: "EPS acceleration = institutional magnet" },
    ],
  },
  {
    label: "Profitability Score",
    max: 30,
    icon: BarChart2,
    color: "text-electric-blue",
    border: "border-electric-blue/20",
    bg: "bg-electric-blue/5",
    items: [
      { metric: "Net Margin ≥ 10%", pts: "+15 pts", note: "Strong pricing power & operational leverage" },
      { metric: "Net Margin > 0%", pts: "+8 pts", note: "At least profitable" },
      { metric: "ROE ≥ 15%", pts: "+15 pts", note: "Efficient capital allocation" },
    ],
  },
  {
    label: "Moat Score",
    max: 20,
    icon: Shield,
    color: "text-amber-400",
    border: "border-amber-400/20",
    bg: "bg-amber-400/5",
    items: [
      { metric: "Wide Economic Moat", pts: "+10 pts", note: "Net margin >20% & gross margin >50%" },
      { metric: "Narrow Economic Moat", pts: "+5 pts", note: "Net margin >10% & gross margin >30%" },
      { metric: "Market Share ≥ 10%", pts: "+10 pts", note: "Estimated from revenue vs. industry" },
      { metric: "Market Share ≥ 5%", pts: "+5 pts", note: "Emerging competitive position" },
    ],
  },
  {
    label: "Health Score",
    max: 20,
    icon: Heart,
    color: "text-rose-400",
    border: "border-rose-400/20",
    bg: "bg-rose-400/5",
    items: [
      { metric: "Debt/Equity < 1.0", pts: "+10 pts", note: "Conservative balance sheet" },
      { metric: "Piotroski F-Score ≥ 7/9", pts: "+10 pts", note: "9-point earnings quality check" },
      { metric: "Piotroski F-Score ≥ 5/9", pts: "+5 pts", note: "Moderate quality" },
    ],
  },
];

const GRADE_BANDS = [
  { grade: "A+", range: "90–100", color: "text-neon-green", bg: "bg-neon-green/10 border-neon-green/30", desc: "Elite institutional quality. Best-of-class fundamentals across all dimensions." },
  { grade: "A",  range: "80–89",  color: "text-neon-green", bg: "bg-neon-green/5 border-neon-green/20",  desc: "Excellent profile. Strong growth + profitability + healthy balance sheet." },
  { grade: "B+", range: "70–79",  color: "text-electric-blue", bg: "bg-electric-blue/10 border-electric-blue/30", desc: "Strong fundamentals with minor gaps. Institutional-grade watchlist." },
  { grade: "B",  range: "60–69",  color: "text-electric-blue", bg: "bg-electric-blue/5 border-electric-blue/20",  desc: "Solid business. Consider accumulating on dips." },
  { grade: "C",  range: "50–59",  color: "text-amber-400", bg: "bg-amber-400/5 border-amber-400/20",      desc: "Mixed fundamentals. High risk vs. reward. Monitor closely." },
  { grade: "D",  range: "40–49",  color: "text-orange-400", bg: "bg-orange-400/5 border-orange-400/20",   desc: "Weak profile. Avoid unless contrarian thesis exists." },
  { grade: "F",  range: "0–39",   color: "text-danger",    bg: "bg-danger/5 border-danger/20",            desc: "Structural fundamental weakness. High risk of capital impairment." },
];

const MOAT_DEFS = [
  { label: "WIDE", color: "text-neon-green", bg: "bg-neon-green/10 border-neon-green/30", desc: "Net Margin > 20% AND Gross Margin > 50%. Consistent pricing power, high barriers to entry, durable competitive advantage." },
  { label: "NARROW", color: "text-electric-blue", bg: "bg-electric-blue/10 border-electric-blue/30", desc: "Net Margin > 10% AND Gross Margin > 30%. Some competitive advantage but more susceptible to disruption." },
  { label: "NONE", color: "text-muted", bg: "bg-white/5 border-white/10", desc: "Margins below threshold. Commoditized business or early-stage with unproven economics." },
];

export default function NomenclaturePanel({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  return (
    <AnimatePresence>
      {isOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-[100] pointer-events-auto cursor-pointer"
          />
          <motion.div
            initial={{ opacity: 0, x: 420 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 420 }}
            transition={{ type: "spring", damping: 28, stiffness: 280 }}
            className="fixed right-0 top-0 bottom-0 w-full max-w-lg bg-[#090C13] border-l border-white/[0.07] z-[101] shadow-2xl overflow-y-auto pointer-events-auto"
          >
            {/* Header */}
            <div className="sticky top-0 bg-[#090C13]/95 backdrop-blur-md border-b border-white/[0.07] px-8 py-5 flex items-center justify-between z-10">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-electric-blue/10 border border-electric-blue/20">
                  <BookOpen className="w-4 h-4 text-electric-blue" />
                </div>
                <div>
                  <h2 className="text-sm font-mono font-black tracking-tighter text-white">METODOLOGÍA</h2>
                  <p className="text-[9px] font-mono text-muted tracking-widest uppercase mt-0.5">Alpha Station v6.0 — Fundamental Engine</p>
                </div>
              </div>
              <button onClick={onClose} className="p-2 rounded-lg hover:bg-white/5 text-muted hover:text-white transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="px-8 py-6 space-y-8">
              {/* Intro */}
              <div className="p-4 rounded-xl bg-white/[0.03] border border-white/[0.06]">
                <div className="flex items-start gap-3">
                  <Info className="w-4 h-4 text-electric-blue mt-0.5 shrink-0" />
                  <p className="text-[11px] text-text-secondary leading-relaxed">
                    Alpha Station analiza empresas exclusivamente con métricas fundamentales. Sin análisis técnico, sin price action, sin momentum de precio. El objetivo: identificar negocios de calidad institucional con ventajas competitivas duraderas.
                  </p>
                </div>
              </div>

              {/* Alpha Score Formula */}
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <Zap className="w-4 h-4 text-neon-green" />
                  <h3 className="text-[11px] font-mono font-black tracking-[0.15em] text-white uppercase">Alpha Score (0–100)</h3>
                </div>

                {/* Score bar visual */}
                <div className="flex items-center gap-1 mb-5 h-2 rounded-full overflow-hidden">
                  <div className="h-full bg-neon-green/80 flex-[30]" title="Growth 30pt" />
                  <div className="h-full bg-electric-blue/80 flex-[30]" title="Profit 30pt" />
                  <div className="h-full bg-amber-400/80 flex-[20]" title="Moat 20pt" />
                  <div className="h-full bg-rose-400/80 flex-[20]" title="Health 20pt" />
                </div>
                <div className="flex text-[9px] font-mono text-muted mb-5 gap-4 flex-wrap">
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-neon-green/80 inline-block"/>Growth 30pts</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-electric-blue/80 inline-block"/>Profitability 30pts</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-400/80 inline-block"/>Moat 20pts</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-400/80 inline-block"/>Health 20pts</span>
                </div>

                <div className="space-y-3">
                  {SCORE_DIMS.map((dim) => {
                    const Icon = dim.icon;
                    return (
                      <div key={dim.label} className={`rounded-xl border ${dim.border} ${dim.bg} p-4`}>
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <Icon className={`w-3.5 h-3.5 ${dim.color}`} />
                            <span className={`text-[10px] font-mono font-black ${dim.color} tracking-widest uppercase`}>{dim.label}</span>
                          </div>
                          <span className="text-[10px] font-mono text-muted">max {dim.max} pts</span>
                        </div>
                        <div className="space-y-2">
                          {dim.items.map((item) => (
                            <div key={item.metric} className="flex items-start justify-between gap-3">
                              <div>
                                <div className="text-[10px] font-mono font-bold text-text-secondary">{item.metric}</div>
                                <div className="text-[9px] text-muted mt-0.5">{item.note}</div>
                              </div>
                              <span className={`text-[10px] font-mono font-black ${dim.color} whitespace-nowrap shrink-0`}>{item.pts}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>

              {/* Grade Bands */}
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <Target className="w-4 h-4 text-electric-blue" />
                  <h3 className="text-[11px] font-mono font-black tracking-[0.15em] text-white uppercase">Escala de Grados</h3>
                </div>
                <div className="space-y-2">
                  {GRADE_BANDS.map((g) => (
                    <div key={g.grade} className={`flex items-start gap-3 p-3 rounded-lg border ${g.bg}`}>
                      <span className={`text-sm font-mono font-black ${g.color} w-8 shrink-0`}>{g.grade}</span>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono text-muted">{g.range} pts</span>
                        </div>
                        <p className="text-[10px] text-muted mt-0.5 leading-relaxed">{g.desc}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Moat */}
              <section>
                <div className="flex items-center gap-2 mb-4">
                  <Shield className="w-4 h-4 text-amber-400" />
                  <h3 className="text-[11px] font-mono font-black tracking-[0.15em] text-white uppercase">Economic Moat (Foso Económico)</h3>
                </div>
                <p className="text-[11px] text-muted leading-relaxed mb-4">
                  Concepto acuñado por Warren Buffett. Representa la capacidad de una empresa de defender sus márgenes y cuota de mercado frente a la competencia a largo plazo.
                </p>
                <div className="space-y-3">
                  {MOAT_DEFS.map((m) => (
                    <div key={m.label} className={`p-3 rounded-xl border ${m.bg}`}>
                      <div className={`text-[10px] font-mono font-black ${m.color} mb-1`}>{m.label}</div>
                      <p className="text-[10px] text-muted leading-relaxed">{m.desc}</p>
                    </div>
                  ))}
                </div>
              </section>

              {/* Piotroski */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <Heart className="w-4 h-4 text-rose-400" />
                  <h3 className="text-[11px] font-mono font-black tracking-[0.15em] text-white uppercase">Piotroski F-Score (0–9)</h3>
                </div>
                <p className="text-[11px] text-muted leading-relaxed mb-3">
                  Sistema de puntuación de calidad de beneficios de Joseph Piotroski (Stanford). 9 criterios binarios evaluando rentabilidad, liquidez y eficiencia operativa.
                </p>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { range: "7–9", label: "ALTA CALIDAD", color: "text-neon-green", bg: "bg-neon-green/10 border-neon-green/20" },
                    { range: "4–6", label: "MODERADO", color: "text-amber-400", bg: "bg-amber-400/5 border-amber-400/20" },
                    { range: "0–3", label: "RIESGO FRAUDE", color: "text-danger", bg: "bg-danger/5 border-danger/20" },
                  ].map((p) => (
                    <div key={p.range} className={`p-3 rounded-lg border text-center ${p.bg}`}>
                      <div className={`text-xs font-mono font-black ${p.color}`}>{p.range}</div>
                      <div className="text-[9px] font-mono text-muted mt-1">{p.label}</div>
                    </div>
                  ))}
                </div>
              </section>

              {/* Recommendation */}
              <section>
                <div className="flex items-center gap-2 mb-3">
                  <Zap className="w-4 h-4 text-neon-green" />
                  <h3 className="text-[11px] font-mono font-black tracking-[0.15em] text-white uppercase">Recomendaciones del Sistema</h3>
                </div>
                <div className="space-y-2">
                  {[
                    { rec: "STRONG BUY", range: "≥ 75 pts", color: "text-neon-green", bg: "bg-neon-green/10 border-neon-green/30" },
                    { rec: "BUY", range: "60–74 pts", color: "text-electric-blue", bg: "bg-electric-blue/5 border-electric-blue/20" },
                    { rec: "HOLD", range: "40–59 pts", color: "text-amber-400", bg: "bg-amber-400/5 border-amber-400/20" },
                    { rec: "AVOID", range: "< 40 pts", color: "text-danger", bg: "bg-danger/5 border-danger/20" },
                  ].map((r) => (
                    <div key={r.rec} className={`flex items-center justify-between px-4 py-2.5 rounded-lg border ${r.bg}`}>
                      <span className={`text-[11px] font-mono font-black ${r.color} tracking-widest`}>{r.rec}</span>
                      <span className="text-[10px] font-mono text-muted">{r.range}</span>
                    </div>
                  ))}
                </div>
              </section>

              <div className="pt-4 border-t border-white/[0.06] text-center">
                <p className="text-[9px] font-mono text-muted uppercase tracking-[0.3em]">Alpha Station Terminal v6.0 — Pure Fundamental Analysis</p>
                <p className="text-[9px] font-mono text-muted/50 mt-1">No technical analysis · No price signals · No momentum</p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
