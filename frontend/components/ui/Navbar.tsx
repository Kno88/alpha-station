"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, BarChart3, Search, Bell, Zap, Menu, BookOpen } from "lucide-react";
import clsx from "clsx";
import { motion } from "framer-motion";
import { useState } from "react";
import NomenclaturePanel from "@/components/NomenclaturePanel";

const NAV_ITEMS = [
  { href: "/", label: "DASHBOARD", icon: BarChart3 },
  { href: "/validator", label: "VALIDATOR", icon: Search },
  { href: "/screener", label: "SCREENER", icon: Activity },
];

export default function Navbar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="fixed top-8 left-0 right-0 z-40 px-6 pointer-events-none pt-4">
      <header className="max-w-screen-2xl mx-auto h-16 glass rounded-2xl px-6 flex items-center justify-between pointer-events-auto border-t border-white/[0.1] border-b border-white/[0.02]">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <motion.div 
            whileHover={{ rotate: 15, scale: 1.1 }}
            className="w-8 h-8 rounded-lg bg-gradient-to-br from-electric-blue to-[#004488] flex items-center justify-center shadow-lg shadow-electric-blue/40 border border-white/20"
          >
            <Zap className="w-4 h-4 text-white fill-current" />
          </motion.div>
          <div className="flex flex-col">
            <span className="font-mono font-black text-sm tracking-tighter text-white leading-none">
              ALPHA<span className="text-neon-green">STATION</span>
            </span>
            <span className="text-[9px] font-mono font-bold text-muted tracking-[0.2em] leading-none mt-1">
              v6.0 INSTITUTIONAL
            </span>
          </div>
        </Link>

        {/* Nav */}
        <nav className="hidden md:flex items-center gap-1">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const isActive = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "relative flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] font-bold font-mono tracking-widest transition-all",
                  isActive
                    ? "text-white"
                    : "text-muted hover:text-text-primary"
                )}
              >
                {isActive && (
                  <motion.div
                    layoutId="nav-pill"
                    className="absolute inset-0 bg-white/10 rounded-lg border border-white/10 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.1)]"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
                <Icon className={clsx("w-3.5 h-3.5 relative z-10", isActive ? "text-electric-blue drop-shadow-[0_0_5px_rgba(59,130,246,0.8)]" : "")} />
                <span className="relative z-10">{label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right side */}
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setIsOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-muted hover:text-white hover:bg-white/10 transition-all group shadow-sm hover:shadow-white/5"
          >
            <BookOpen className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" />
            <span className="text-[10px] font-mono font-bold tracking-widest uppercase">Methodology</span>
          </button>

          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/40 border border-white/5 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]">
            <div className="w-1.5 h-1.5 rounded-full bg-neon-green shadow-[0_0_8px_#10B981] animate-pulse" />
            <span className="text-[10px] text-neon-green font-mono font-bold tracking-widest uppercase text-glow-green">Live Data</span>
          </div>
          
          <button className="md:hidden text-white">
            <Menu className="w-5 h-5" />
          </button>
        </div>
      </header>

      <NomenclaturePanel isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </div>
  );
}
