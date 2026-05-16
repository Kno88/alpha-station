"use client";

import { useEffect, useState } from "react";
import { format } from "date-fns";

export default function StatBar() {
  const [time, setTime] = useState<Date | null>(null);

  useEffect(() => {
    setTime(new Date());
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);

  const isMarketOpen = time ? (() => {
    const h = time.getHours();
    const m = time.getMinutes();
    const mins = h * 60 + m;
    const day = time.getDay();
    return day >= 1 && day <= 5 && mins >= 9 * 60 + 30 && mins < 16 * 60;
  })() : false;

  return (
    <div className="hidden md:flex items-center gap-4 text-xs font-mono">
      <div className="flex items-center gap-1.5">
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            isMarketOpen ? "bg-neon-green animate-pulse" : "bg-muted"
          }`}
        />
        <span className={isMarketOpen ? "text-neon-green" : "text-muted"}>
          {isMarketOpen ? "MARKET OPEN" : "MARKET CLOSED"}
        </span>
      </div>
      <div className="text-muted border-l border-border pl-4">
        {time ? format(time, "HH:mm:ss") : "--:--:--"} EST
      </div>
    </div>
  );
}
