/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['Outfit', 'sans-serif'],
      },
      colors: {
        'card-productivity': '#8B5CF6', // Purple
        'card-wellness': '#14B8A6',     // Teal
        'card-study': '#3B82F6',        // Blue
        'card-meal': '#10B981',         // Green
        'card-shopping': '#F59E0B',     // Mustard
      }
    },
  },
  plugins: [],
}
