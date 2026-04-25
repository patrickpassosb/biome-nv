/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#0a0a0a',
        surface: '#141414',
        border: '#262626',
        'on-surface': '#f0e0d1',
        'on-surface-variant': '#d8c3ad',
        primary: '#ffc174',
        'primary-container': '#f59e0b',
        'on-primary': '#472a00',
        'surface-container': '#261e15',
        'surface-container-low': '#221a12',
        'surface-container-high': '#31281f',
        'surface-bright': '#41382e',
        'outline-variant': '#534434',
        outline: '#a08e7a',
        secondary: '#adc6ff',
        'secondary-container': '#0566d9',
        'on-secondary': '#002e6a',
        tertiary: '#8fd5ff',
        'tertiary-container': '#1abdff',
        'on-tertiary': '#00344a',
        error: '#ffb4ab',
        'error-container': '#93000a',
        'on-error': '#690005',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['Space Grotesk', 'monospace'],
      },
      borderRadius: {
        lg: '0.5rem',
        xl: '0.75rem',
      }
    },
  },
  plugins: [],
}
