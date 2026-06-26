import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // BMW Density colour tokens
        bmw: {
          blue:       "#1c69d4",
          "blue-dark":"#0653b6",
          "blue-light":"#5b9cf6",
          black:      "#1a1a1a",
          white:      "#ffffff",
          grey:       "#767676",
          "grey-light":"#f0f0f0",
          "grey-mid": "#cccccc",
          silver:     "#e8e8e8",
          green:      "#22c55e",
          orange:     "#f97316",
          red:        "#ef4444",
          yellow:     "#eab308",
        },
        // Semantic aliases used throughout the app
        surface: {
          DEFAULT: "#0f1117",   // main background
          raised:  "#1a1d27",   // panels, sidebar
          overlay: "#252836",   // cards, inputs
          border:  "#2e3244",   // dividers
        },
      },
      fontFamily: {
        sans: ["BMWTypeNextPro", "Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "pulse-slow": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in":    "fadeIn 0.15s ease-out",
        "slide-in":   "slideIn 0.2s ease-out",
      },
      keyframes: {
        fadeIn:  { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideIn: { "0%": { transform: "translateX(-8px)", opacity: "0" }, "100%": { transform: "translateX(0)", opacity: "1" } },
      },
    },
  },
  plugins: [
    require("@tailwindcss/typography"),
  ],
} satisfies Config;
