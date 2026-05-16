import type { Config } from "tailwindcss";

export default {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Institutional Dark Palette (Premium) ───────────────────────────
        background: "#050505",
        oxford: {
          DEFAULT: "#0A0A0A",
          50: "#262626",
          100: "#171717",
          200: "#0A0A0A",
          300: "#050505",
        },
        neon: {
          green: "#10B981", // Emerald green, more premium than pure #00FF87
          "green-dim": "#059669",
        },
        electric: {
          blue: "#3B82F6", // Softer, more modern blue
          "blue-dim": "#2563EB",
        },
        amber: "#F59E0B",
        danger: "#EF4444",
        muted: "#737373", // Neutral gray
        "card-bg": "rgba(23, 23, 23, 0.4)",
        border: "rgba(255, 255, 255, 0.08)",
        "text-primary": "#F8FAFC",
        "text-secondary": "#94A3B8",
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "'Fira Code'", "Consolas", "monospace"],
        sans: ["'Inter'", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-in": "slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
        "fade-in": "fadeIn 0.3s ease-out",
        "glow-green": "glowGreen 2s ease-in-out infinite alternate",
        "glow-blue": "glowBlue 2s ease-in-out infinite alternate",
        "ticker": "ticker 30s linear infinite",
        "shimmer": "shimmer 2s linear infinite",
      },
      keyframes: {
        slideIn: {
          from: { transform: "translateY(10px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        glowGreen: {
          from: { textShadow: "0 0 5px rgba(16, 185, 129, 0.5)" },
          to: { textShadow: "0 0 15px rgba(16, 185, 129, 0.8), 0 0 25px rgba(16, 185, 129, 0.5)" },
        },
        glowBlue: {
          from: { textShadow: "0 0 5px rgba(59, 130, 246, 0.5)" },
          to: { textShadow: "0 0 15px rgba(59, 130, 246, 0.8), 0 0 25px rgba(59, 130, 246, 0.5)" },
        },
        ticker: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
        shimmer: {
          from: { backgroundPosition: "200% 0" },
          to: { backgroundPosition: "-200% 0" },
        },
      },
      boxShadow: {
        "neon-green": "0 0 15px rgba(16, 185, 129, 0.2)",
        "electric-blue": "0 0 15px rgba(59, 130, 246, 0.2)",
        card: "0 8px 32px rgba(0, 0, 0, 0.4)",
        glass: "inset 0 1px 0 0 rgba(255, 255, 255, 0.05)",
      },
      backgroundImage: {
        'glass-gradient': 'linear-gradient(to bottom right, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.01))',
        'shimmer-gradient': 'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.05) 50%, rgba(255,255,255,0) 100%)',
      }
    },
  },
  plugins: [],
} satisfies Config;
