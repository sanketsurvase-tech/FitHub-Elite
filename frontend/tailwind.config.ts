import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#121915",
        muted: "#77827c",
        line: "#e8ece8",
        lime: "#c5f36b",
        forest: "#163b2a",
      },
      boxShadow: {
        soft: "0 12px 40px rgba(24, 42, 31, .06)",
      },
    },
  },
  plugins: [],
};

export default config;
