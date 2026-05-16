"use client";

import React, { useEffect, useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import { api, MarketTapeItem } from "@/lib/api";

export default function TickerTape() {
  const [marketData, setMarketData] = useState<MarketTapeItem[]>([]);

  useEffect(() => {
    let mounted = true;
    const fetchData = async () => {
      try {
        const data = await api.marketTape();
        if (mounted && data.length > 0) {
          setMarketData(data);
        }
      } catch {
        // Falls back to mock data — no action needed
      }
    };
    fetchData();
    const interval = setInterval(fetchData, 60000); // refresh every minute
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  // Use mock data as fallback while loading or if error
  const displayData = marketData.length > 0 ? marketData : [
    { symbol: "SPY", price: 524.12, change: 1.25, percent: 0.24 },
    { symbol: "QQQ", price: 445.67, change: 2.10, percent: 0.47 },
    { symbol: "DIA", price: 390.15, change: 0.85, percent: 0.22 },
    { symbol: "AAPL", price: 178.44, change: 1.22, percent: 0.69 },
    { symbol: "MSFT", price: 420.55, change: 3.45, percent: 0.83 },
    { symbol: "NVDA", price: 890.12, change: -12.4, percent: -1.37 },
  ];
  return (
    <div className="sticky top-0 z-50 w-full bg-[#080B10] border-b border-white/[0.06] overflow-hidden flex items-center h-8">
      <div className="flex whitespace-nowrap animate-ticker">
        {/* We duplicate the items to make the infinite scroll seamless */}
        {[...displayData, ...displayData, ...displayData].map((item, index) => {
          const isPositive = item.change >= 0;
          return (
            <div
              key={`${item.symbol}-${index}`}
              className="flex items-center gap-2 px-6 border-r border-border/50 text-[11px] font-mono"
            >
              <span className="font-bold text-text-primary">{item.symbol}</span>
              <span className="text-text-secondary">${item.price.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
              <span className={`flex items-center gap-1 ${isPositive ? 'text-neon-green' : 'text-danger'}`}>
                {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                {isPositive ? '+' : ''}{item.change.toFixed(2)} ({isPositive ? '+' : ''}{item.percent.toFixed(2)}%)
              </span>
            </div>
          );
        })}
      </div>
      {/* Gradients to fade edges */}
      <div className="absolute left-0 top-0 bottom-0 w-12 bg-gradient-to-r from-oxford-100 to-transparent z-10"></div>
      <div className="absolute right-0 top-0 bottom-0 w-12 bg-gradient-to-l from-oxford-100 to-transparent z-10"></div>
    </div>
  );
}
