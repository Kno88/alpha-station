"use client";

import { useEffect, useState, useRef } from "react";
import { toast } from "react-toastify";
import { api, AlertEvent } from "@/lib/api";
import { Bell, BellRing, X, TrendingUp, Zap, Activity } from "lucide-react";
import clsx from "clsx";

const ALERT_ICONS: Record<string, React.ReactNode> = {
  STAGE2_BREAKOUT: <TrendingUp className="w-3.5 h-3.5" />,
  STAGE2_TRANSITION: <Activity className="w-3.5 h-3.5" />,
  GEX_FLIP: <Zap className="w-3.5 h-3.5" />,
};

const SEVERITY_STYLES: Record<string, string> = {
  HIGH: "bg-neon-green/5 border-neon-green/30 text-neon-green",
  MEDIUM: "bg-amber/5 border-amber/30 text-amber",
  LOW: "bg-electric-blue/5 border-electric-blue/30 text-electric-blue",
};

export default function AlertBanner() {
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [visible, setVisible] = useState(true);
  const [expanded, setExpanded] = useState(false);
  const seenIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    const poll = async () => {
      try {
        const fresh = await api.alerts();
        const newAlerts = fresh.filter((a) => {
          const id = `${a.ticker}:${a.alert_type}:${a.timestamp}`;
          if (seenIds.current.has(id)) return false;
          seenIds.current.add(id);
          return true;
        });

        if (newAlerts.length > 0) {
          setAlerts((prev) => [...newAlerts, ...prev].slice(0, 20));
          newAlerts.forEach((a) => {
            if (a.severity === "HIGH") {
              toast.success(a.message, { autoClose: 8000 });
            }
          });
        }
      } catch {
        // Silent — don't spam errors on polling
      }
    };

    poll();
    const id = setInterval(poll, 60_000); // Poll every minute
    return () => clearInterval(id);
  }, []);

  if (alerts.length === 0 || !visible) return null;

  const highAlerts = alerts.filter((a) => a.severity === "HIGH");
  const displayAlerts = expanded ? alerts : alerts.slice(0, 3);

  return (
    <div className="sticky top-16 z-40 max-w-screen-2xl mx-auto px-4 pt-3">
      <div className="rounded-xl border border-neon-green/20 bg-oxford-100 shadow-neon-green overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
          <div className="flex items-center gap-2">
            {highAlerts.length > 0 ? (
              <BellRing className="w-4 h-4 text-neon-green animate-pulse" />
            ) : (
              <Bell className="w-4 h-4 text-amber" />
            )}
            <span className="text-xs font-mono font-semibold text-text-primary">
              ACTIVE ALERTS
            </span>
            <span className="px-1.5 py-0.5 rounded-full bg-neon-green/10 text-neon-green text-xs font-mono font-bold">
              {alerts.length}
            </span>
            {highAlerts.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-danger/10 text-danger text-xs font-mono">
                {highAlerts.length} HIGH
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-xs text-muted hover:text-electric-blue font-mono transition-colors"
            >
              {expanded ? "collapse" : `+${alerts.length - 3} more`}
            </button>
            <button
              onClick={() => setVisible(false)}
              className="text-muted hover:text-danger transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Alert rows */}
        <div className="divide-y divide-border/40">
          {displayAlerts.map((alert, i) => (
            <div
              key={i}
              className={clsx(
                "flex items-center gap-3 px-4 py-2.5 text-xs font-mono transition-colors",
                SEVERITY_STYLES[alert.severity]
              )}
            >
              <span className="flex-shrink-0">
                {ALERT_ICONS[alert.alert_type] ?? <Bell className="w-3.5 h-3.5" />}
              </span>
              <span className="font-bold min-w-[40px]">{alert.ticker}</span>
              <span className="flex-1 text-text-secondary">{alert.message}</span>
              <span className="text-muted flex-shrink-0">
                {new Date(alert.timestamp).toLocaleTimeString()}
              </span>
              <span
                className={clsx(
                  "px-1.5 py-0.5 rounded text-xs uppercase font-bold",
                  alert.severity === "HIGH"
                    ? "bg-neon-green/10 text-neon-green"
                    : alert.severity === "MEDIUM"
                    ? "bg-amber/10 text-amber"
                    : "bg-electric-blue/10 text-electric-blue"
                )}
              >
                {alert.severity}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
