/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── V2 "Unlock" brand palette ──────────────────────────────────────
        // Anchored on the legacy logo orange (#FF6F00 — the keyhole graduation
        // cap). This is the only brand colour; the legacy `primary` blue was
        // retired in M6-02 once every authenticated surface moved to `brand`.
        brand: {
          50: '#FFF8F1',
          100: '#FFEEDC',
          200: '#FED7AA',
          300: '#FDBA74',
          400: '#FB8E3C',
          500: '#FB7705',
          600: '#FF6F00', // ← brand anchor (legacy logo orange)
          700: '#CC5800',
          800: '#9E4500',
          900: '#7A3500',
        },
        // Chalkboard-heritage neutrals: warm ink for surfaces, soft chalk for
        // foreground on dark. A nod to the legacy blackboard motif.
        ink: {
          50: '#F6F5F4',
          100: '#E7E5E2',
          200: '#C9C5BF',
          300: '#A29C93',
          400: '#736D63',
          500: '#4A463F',
          600: '#34302B',
          700: '#252220',
          800: '#1A1816',
          900: '#0F0E0D',
        },
      },
      fontFamily: {
        // Noto Sans Devanagari sits behind Inter/Fraunces: neither covers
        // Devanagari, so Hindi glyphs (the hi locale, हिन्दी in copy) fall
        // through to it instead of an unstyled system font.
        sans: ['Inter', '"Noto Sans Devanagari"', 'system-ui', 'sans-serif'],
        display: ['"Fraunces"', '"Noto Sans Devanagari"', 'Georgia', 'serif'],
      },
      boxShadow: {
        // Warm-toned elevation (ink, not cold black) — the V2 surface system.
        soft: '0 1px 2px rgba(26,24,22,0.04), 0 4px 16px rgba(26,24,22,0.06)',
        card: '0 1px 3px rgba(26,24,22,0.05), 0 10px 30px -12px rgba(26,24,22,0.12)',
        lift: '0 18px 40px -16px rgba(255,111,0,0.40)',
        chalk: 'inset 0 1px 0 rgba(255,255,255,0.04)',
      },
      borderRadius: {
        xl2: '1.25rem',
        '3xl': '1.75rem',
      },
      keyframes: {
        'fade-up': {
          '0%': { opacity: '0', transform: 'translateY(14px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        float: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-7px)' },
        },
      },
      animation: {
        'fade-up': 'fade-up 0.6s cubic-bezier(0.22,1,0.36,1) both',
        'fade-in': 'fade-in 0.5s ease both',
        float: 'float 7s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
