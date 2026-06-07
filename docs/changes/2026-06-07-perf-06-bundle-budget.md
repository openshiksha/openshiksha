# PERF-06 — CI bundle-size budget guard

**Date:** 2026-06-07
**Initiative:** Performance Budget
**Classification:** New

## Summary

Locks in the entry-chunk cuts landed in PERF-01..PERF-04 with a CI-enforced
budget. Adds:
- `frontend_modern/scripts/check-bundle-budget.mjs` — reads `dist/index.html`,
  resolves the hashed entry chunk filename (never hard-coded), compares its
  size to `DEFAULT_BUDGET_BYTES = 160 * 1024`, exits non-zero on overage with a
  clear over-by-X message pointing at how to raise the ceiling deliberately.
- `frontend_modern/scripts/check-bundle-budget.test.mjs` — 9 unit tests
  covering `findEntryChunk` (parsing index.html), `formatBytes`, and the pure
  `checkBudget` decision function (pass / boundary / fail).
- `npm run check:budget` script.
- `docs/perf/budget.md` — the ceiling, the CI plumbing, the raise-the-ceiling
  protocol, and a dated history table.
- A new CI step in `.github/workflows/ci-cd.yaml`'s `frontend` job that runs
  `npm run check:budget` after `npm run build`.

## Why 160 kB?

Post-PERF-04 the entry chunk measures ~129 kB uncompressed. 160 kB gives ~24%
headroom — enough to absorb routine feature growth without paging on every PR,
small enough that any sustained drift triggers a forced conversation. The
protocol in `docs/perf/budget.md` requires every ceiling bump to either avoid
itself via lazy-loading or be documented in the history table.

## Verification

- `npm run check:budget` on a fresh post-PERF-04 build —
  `OK — assets/index-ijK6y_PY.js is 128.99 kB (budget 160.00 kB, headroom 31.01 kB).`
- `npm test -- --run` — 32 files / 203 tests pass (9 new for the script).
- Synthetic overage tested via `checkBudget({ sizeBytes: 200kB, budgetBytes: 160kB })`
  — asserts a `FAIL` result and the raise-the-ceiling pointer.

## Next steps

PERF-05 (font-loading optimization) is the obvious next pull. The budget guard
will now defend whatever ceiling PERF-05 lands.
