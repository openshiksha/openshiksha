export default {
  plugins: {
    // Tailwind v4 ships its PostCSS integration as a separate package, and now
    // handles @import inlining + vendor prefixing itself (postcss-import and
    // autoprefixer are no longer needed).
    '@tailwindcss/postcss': {},
  },
}
