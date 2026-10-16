/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        soc: {
          dark: "#0b1015",
          panel: "#111827",
          border: "#1f2937",
          accent: "#22d3ee",
          danger: "#ef4444",
          warning: "#f59e0b",
          success: "#22c55e",
        },
      },
      fontFamily: {
        sans: ["ui-sans-serif", "system-ui", "Segoe UI", "Roboto", "Helvetica", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
}