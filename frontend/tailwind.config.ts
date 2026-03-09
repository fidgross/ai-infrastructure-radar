import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./types/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: "#11212d",
        mist: "#f4efe7",
        ember: "#d95d39",
        moss: "#48644d",
        slate: "#435b66"
      },
      boxShadow: {
        panel: "0 20px 60px rgba(17, 33, 45, 0.12)"
      }
    }
  },
  plugins: []
};

export default config;
