# PERF-02 — Drop unused `recharts` dependency

**Date:** 2026-06-07
**Initiative:** Performance Budget
**Classification:** Improve

## Summary

Removes the `recharts` package from `frontend_modern/package.json`. It was a
holdover from an early scaffolding decision — proficiency / trend charts in the
modern stack are hand-rolled SVG (see `StudentProficiencySnapshot` sparklines in
`ParentInsightsPage`, the proficiency page graph, etc.), and recharts is
imported **nowhere** in `frontend_modern/` (src, scripts, widgets, or e2e).

## Verification

- `grep -rn recharts frontend_modern/` returns no source matches (only the
  package.json line being removed and unrelated planning docs).
- `grep -ri "recharts\|LineChart\|BarChart\|AreaChart\|PieChart"` across all
  `.ts/.tsx/.mjs/.js` in `frontend_modern/` returns nothing.
- `npm ls recharts` after install reports `(empty)`.
- `npm run type-check` — green.
- `npm run lint` — green.
- `npm test -- --run` — 31 files / 194 tests pass.
- `npm run build` — green.

## Tests

No new tests required; this is pure dead-weight removal.

## Next steps

PERF-03 (route-level lazy) is the big entry-chunk cut.
