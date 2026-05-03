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
        // ── Institutional Dark Palette ─────────────────────────────────────
        oxford: {
          DEFAULT: "#1C2333",
          50: "#2D3A52",
          100: "#242E42",
          200: "#1C2333",
          300: "#141B28",
        },
        neon: {
          green: "#00FF87",
          "green-dim": "#00CC6A",
        },
        electric: {
          blue: "#0088FF",
          "blue-dim": "#0066CC",
        },
        amber: "#FFB800",
        danger: "#FF4560",
        muted: "#6B7A99",
        "card-bg": "#242E42",
        border: "#2D3A52",
        "text-primary": "#E8EBF0",
        "text-secondary": "#A0AECB",
      },
      fontFamily: {
        mono: ["'JetBrains Mono'", "'Fira Code'", "Consolas", "monospace"],
        sans: ["'Inter'", "system-ui", "sans-serif"],
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slide-in": "slideIn 0.3s ease-out",
        "fade-in": "fadeIn 0.2s ease-out",
        glow: "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        slideIn: {
          from: { transform: "translateY(-10px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        glow: {
          from: { textShadow: "0 0 5px #00FF87, 0 0 10px #00FF87" },
          to: { textShadow: "0 0 15px #00FF87, 0 0 25px #00FF87" },
        },
      },
      boxShadow: {
        "neon-green": "0 0 10px rgba(0, 255, 135, 0.3)",
        "electric-blue": "0 0 10px rgba(0, 136, 255, 0.3)",
        card: "0 4px 24px rgba(0, 0, 0, 0.4)",
      },
    },
  },
  plugins: [],
} satisfies Config;
