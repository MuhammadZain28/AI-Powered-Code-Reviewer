/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        dark: {
          bg: '#0d1117',
          card: '#161b22',
          border: '#30363d',
          text: '#c9d1d9',
          textSecondary: '#8b949e',
          hover: '#1f2428',
        }
      },
      severity: {
        critical: '#f85149',
        high: '#da3633',
        medium: '#e3b341',
        low: '#3fb950',
      }
    },
  },
  plugins: [],
}