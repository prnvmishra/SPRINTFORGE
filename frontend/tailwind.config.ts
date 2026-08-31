import type { Config } from "tailwindcss";

/**
 * SprintForge design tokens.
 *
 * Dark-first, single accent. The accent (signal lime) is reserved for primary
 * actions, active state, live system activity and progress — never decoration.
 * Semantic colours sit in different hue families so a status can never be
 * confused with the accent.
 */
const config: Config = {
  darkMode: "class",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#08080a",
        surface: "#0d0e11",
        elevated: "#14161a",
        raised: "#1b1e23",
        line: "#1f2228",
        "line-strong": "#2c3138",
        faint: "#5b616b",
        muted: "#8a9099",
        ink: "#f1f2ef",
        accent: {
          DEFAULT: "#c8fa4b",
          dim: "#a9d92f",
          soft: "#dcfd8b",
          ink: "#0a0c06",
        },
        success: "#3ddc97",
        warning: "#f5b544",
        danger: "#ff6156",
        info: "#7cc4ff",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "var(--font-sans)", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      fontSize: {
        // Editorial display sizes clamp so the hero never breaks on small screens.
        "display-xl": ["clamp(2.6rem, 7.4vw, 7rem)", { lineHeight: "0.92", letterSpacing: "-0.04em" }],
        "display-lg": ["clamp(2.5rem, 7vw, 5.5rem)", { lineHeight: "0.94", letterSpacing: "-0.035em" }],
        "display-md": ["clamp(1.9rem, 4.2vw, 3.25rem)", { lineHeight: "1.02", letterSpacing: "-0.03em" }],
        "display-sm": ["clamp(1.5rem, 2.6vw, 2.1rem)", { lineHeight: "1.08", letterSpacing: "-0.02em" }],
      },
      borderRadius: {
        // Radius is used sparingly; nothing larger than a subtle 10px.
        sm: "3px",
        DEFAULT: "5px",
        md: "6px",
        lg: "8px",
        xl: "10px",
      },
      boxShadow: {
        panel: "0 1px 0 rgba(255,255,255,0.02) inset, 0 24px 60px -32px rgba(0,0,0,0.9)",
        lift: "0 32px 80px -40px rgba(0,0,0,0.95)",
        "accent-glow": "0 0 0 1px rgba(200,250,75,0.28), 0 18px 50px -22px rgba(200,250,75,0.3)",
      },
      transitionTimingFunction: {
        // One shared easing keeps every motion in the product feeling related.
        forge: "cubic-bezier(0.16, 1, 0.3, 1)",
      },
      keyframes: {
        reveal: {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "reveal-blur": {
          from: { opacity: "0", filter: "blur(6px)", transform: "translateY(14px)" },
          to: { opacity: "1", filter: "blur(0)", transform: "translateY(0)" },
        },
        "line-grow": {
          from: { transform: "scaleX(0)" },
          to: { transform: "scaleX(1)" },
        },
        "dash-flow": {
          to: { strokeDashoffset: "-24" },
        },
        "pulse-ring": {
          "0%": { opacity: "0.5", transform: "scale(0.85)" },
          "70%,100%": { opacity: "0", transform: "scale(1.9)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        caret: {
          "0%,49%": { opacity: "1" },
          "50%,100%": { opacity: "0" },
        },
        marquee: {
          from: { transform: "translateX(0)" },
          to: { transform: "translateX(-50%)" },
        },
        "scan-down": {
          from: { transform: "translateY(-100%)" },
          to: { transform: "translateY(400%)" },
        },
      },
      animation: {
        reveal: "reveal 520ms cubic-bezier(0.16,1,0.3,1) both",
        "reveal-blur": "reveal-blur 640ms cubic-bezier(0.16,1,0.3,1) both",
        "line-grow": "line-grow 700ms cubic-bezier(0.16,1,0.3,1) both",
        "dash-flow": "dash-flow 900ms linear infinite",
        "pulse-ring": "pulse-ring 2.4s cubic-bezier(0.16,1,0.3,1) infinite",
        shimmer: "shimmer 1.8s linear infinite",
        caret: "caret 1.1s steps(1) infinite",
        marquee: "marquee 38s linear infinite",
        "scan-down": "scan-down 2.6s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;
