"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Activity, BarChart3, Search, Bell, Zap } from "lucide-react";
import clsx from "clsx";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: BarChart3 },
  { href: "/validator", label: "Validator", icon: Search },
  { href: "/screener", label: "Screener", icon: Activity },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-oxford-200/95 backdrop-blur-sm border-b border-border h-16">
      <div className="max-w-screen-2xl mx-auto h-full px-4 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="w-7 h-7 rounded bg-electric-blue/10 border border-electric-blue/30 flex items-center justify-center">
            <Zap className="w-4 h-4 text-electric-blue group-hover:text-neon-green transition-colors" />
          </div>
          <span className="font-mono font-bold text-sm text-text-primary">
            ALPHA<span className="text-neon-green">STATION</span>
            <span className="text-muted ml-1">v4.0</span>
          </span>
        </Link>

        {/* Nav */}
        <nav className="flex items-center gap-1">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium font-mono transition-all",
                pathname === href
                  ? "bg-electric-blue/10 text-electric-blue border border-electric-blue/20"
                  : "text-muted hover:text-text-primary hover:bg-oxford-50/50"
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {label}
            </Link>
          ))}
        </nav>

        {/* Right side */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-neon-green animate-pulse" />
            <span className="text-xs text-muted font-mono">LIVE</span>
          </div>
        </div>
      </div>
    </header>
  );
}
