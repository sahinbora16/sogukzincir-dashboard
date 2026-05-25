/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        sogukzincir: {
          blue:         '#0f4c81',
          'blue-light': '#dde8f3',
          'blue-dark':  '#093666',
          green:        '#1a7a4a',
          'green-light': '#d0edd9',
          'green-dark':  '#0f5c35',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
