/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#EBF0F8',
          100: '#D4DFEF',
          200: '#A9BFE0',
          300: '#7E9FD0',
          400: '#537FC1',
          500: '#2E5EAA',
          600: '#254B88',
          700: '#1C3866',
          800: '#132544',
          900: '#0A1322',
        },
        accent: {
          50: '#FFF5EB',
          100: '#FFE6CC',
          200: '#FFCC99',
          300: '#FFB366',
          400: '#F7941D',
          500: '#E0850F',
          600: '#B96B0C',
          700: '#915209',
          800: '#693A06',
          900: '#412204',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', '"Noto Sans SC"', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
