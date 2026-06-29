# 2026-06-28 — Frontend coverage thresholds ratcheted to measured

**Classification:** Test infrastructure (tightens an existing, stale gate — no
product code touched).

## Summary
The Vitest coverage thresholds in `frontend_modern/vite.config.ts` were still set
to the **10 / 10 / 6 / 8** floor baselined on 2026-06-01, when the suite had **38
tests**. The suite has since grown to **566 tests across 83 files**, and real
measured coverage is now **56.27 % lines / 55.40 % statements / 51.26 % functions
/ 55.47 % branches** — roughly 5–6× the gate. The floor no longer protected
against regression at all: a PR could delete the bulk of the frontend tests, or
ship a large untested feature, and CI would stay green all the way down to 10 %.

This raises the thresholds to sit ~1 point under the current measured coverage:

| Metric     | Old | New | Measured |
|------------|----:|----:|---------:|
| Lines      | 10  | 55  | 56.27    |
| Statements | 10  | 54  | 55.40    |
| Functions  | 6   | 50  | 51.26    |
| Branches   | 8   | 54  | 55.47    |

## Why a ~1-point buffer (not the exact measured value)
A small gap between the threshold and the measured value absorbs ordinary PR
churn — e.g. a PR that adds a small untested utility shouldn't turn the coverage
gate red on its own — while still failing fast on a real regression (deleted
tests, large untested code). The thresholds remain a **ratchet**: raise them as
new tests land, never lower without a recorded reason (the existing comment in
`vite.config.ts` states this).

## Verification
`npx vitest run --coverage` — 566 tests pass, coverage summary unchanged
(55.4 / 55.47 / 51.26 / 56.27), exit 0 with the new thresholds enforced.

## Files changed
- `frontend_modern/vite.config.ts` — `test.coverage.thresholds` raised from
  10/10/6/8 to 55/54/50/54; comment updated with the new baseline and rationale.
