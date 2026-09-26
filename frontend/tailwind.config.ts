import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#F6F8FC",
        foreground: "#101828",
        workspace: "#F6F8FC",
        navy: {
          900: "#0B1224",
          950: "#080D1A",
        },
        slate: {
          50: "#F8FAFC",
          100: "#F1F5F9",
          200: "#E2E8F0",
          300: "#CBD5E1",
          400: "#94A3B8",
          500: "#64748B",
          600: "#475569",
          700: "#334155",
          800: "#1E293B",
          900: "#0F172A",
        },
        indigo: {
          50: "#EEF2FF",
          100: "#E0E7FF",
          200: "#C7D2FE",
          500: "#6366F1",
          600: "#4F46E5",
          700: "#4338CA",
        },
      },
      boxShadow: {
        card: "0 1px 3px 0 rgba(16, 24, 40, 0.04), 0 1px 2px 0 rgba(16, 24, 40, 0.02)",
        "card-hover": "0 4px 12px 0 rgba(16, 24, 40, 0.06), 0 1px 3px 0 rgba(16, 24, 40, 0.04)",
      },
      borderRadius: {
        "2xl": "16px",
      },
    },
  },
  plugins: [],
};
export default config;
