# PERF-01 — Measurement harness + vendor `manualChunks`

**Date:** 2026-06-07
**Initiative:** Performance Budget (`docs/initiatives/performance-budget.md`)
**Classification:** Improve

## Summary

Foundation PR for the Performance Budget batch. Adds the measurement harness
(`rollup-plugin-visualizer` behind a `--mode analyze` flag), splits framework
vendor code into long-cacheable chunks via `rollupOptions.output.manualChunks`,
and records the first baseline in `docs/perf/baseline-2026-06-07.md`. No app
code paths touched — only the build config.

## Legacy files referenced

None — this is purely a build-system improvement; the legacy Django stack had
no SPA bundle.

## What changed and why

- **`frontend_modern/vite.config.ts`** — switched to the factory form
  `defineConfig(({ mode }) => …)` so the visualizer plugin can opt in via
  `--mode analyze`. Added `rollupOptions.output.manualChunks` (function form —
  rolldown requires a function, not the object shorthand) grouping
  `react / react-dom / react-router-dom / scheduler` → `vendor-react`,
  `@tanstack/*` → `vendor-query`, `katex / react-katex` → `vendor-katex`, and
  `dompurify` → `vendor-dompurify`. Set `chunkSizeWarningLimit: 900` as the
  honest current ceiling (PERF-03 will drop it; PERF-06 will enforce a budget).
- **`frontend_modern/package.json`** — added `rollup-plugin-visualizer` devDep
  and a `build:analyze` script.
- **`docs/perf/baseline-2026-06-07.md`** (new) — records before/after entry-
  chunk sizes (855 kB → 353 kB / 247 kB → 92 kB gzip) and how to reproduce.

## Results

| Asset                       | Before    | After     |
| --------------------------- | --------- | --------- |
| Entry `index-*.js`          | 855.15 kB | 353.05 kB |
| Entry `index-*.js` (gzip)   | 247.44 kB |  91.53 kB |

Vendor chunks now total ~550 kB but are content-hashed and cache-stable across
any feature-code change.

## Tests

- `npm run build` — green, vendor chunks emitted, no warnings.
- `npm run build:analyze` — emits `dist/stats.html`.
- `npm test -- --run` — 31 files / 194 tests pass.

## Migration notes

None.

## Next steps

PERF-02 (drop unused `recharts`), PERF-03 (route-level lazy), PERF-04 (lazy
KaTeX), PERF-06 (CI budget guard) all measure against this baseline.
