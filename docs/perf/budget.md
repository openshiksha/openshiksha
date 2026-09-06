# Frontend bundle-size budget (PERF-06)

This budget is a *contract*. Every PR that ships frontend code must keep the
entry JS chunk under the ceiling, otherwise CI fails. The whole point is to
prevent silent regression of the cuts landed in PERF-01..PERF-04.

> This guards *static bytes*. For the *runtime* side — LCP / TBT / CLS on a
> throttled mobile profile — see the [Lighthouse CI budget](lighthouse.md)
> (PERF-07).

## Current ceiling

| Asset                  | Ceiling | Measured (post-PERF-04) |
| ---------------------- | ------- | ----------------------- |
| `dist/assets/index-*.js` (entry) | **180 kB** | ~161 kB |

The "entry" is whatever `dist/index.html` references as
`<script type="module" src="/assets/*.js">`. Hash-renamed each build; the
guard resolves the name from `index.html`, never hard-codes it.

## How CI enforces it

The frontend job runs `npm run check:budget` after `npm run build` (see
`.github/workflows/ci-cd.yaml`). The script
(`frontend_modern/scripts/check-bundle-budget.mjs`) reads `dist/index.html`,
finds the entry chunk, and compares its size to `DEFAULT_BUDGET_BYTES`. Exit
non-zero on overage. Unit-tested via `check-bundle-budget.test.mjs`.

## Running it locally

```bash
cd frontend_modern
npm run build
npm run check:budget                  # prints OK / FAIL
npm run check:budget -- --budget=131072   # one-off override (128 kB)
```

## Raise-the-ceiling protocol

Don't quietly bump the budget. When a deliberate, justified change pushes the
entry chunk past the ceiling:

1. **Try to avoid the bump first.** Can the new code be lazy-loaded behind a
   route, behind a user action, or behind a feature flag? PERF-03's
   `React.lazy` pattern is the default tool.
2. If the bump is genuinely warranted, edit `DEFAULT_BUDGET_BYTES` in
   `frontend_modern/scripts/check-bundle-budget.mjs`.
3. Add a row to the **history** section below with the date, the new ceiling,
   the measured entry size, and the reason.
4. Ship the budget bump in its own PR (or call it out clearly in the PR that
   needs it). Reviewers should be able to see the budget change without
   hunting.

## History

| Date       | Ceiling | Measured | Reason                                |
| ---------- | ------- | -------- | ------------------------------------- |
| 2026-06-07 | 160 kB  | 129 kB   | PERF-06 initial set after PERF-01..04. |
| 2026-09-06 | 180 kB  | 161 kB   | Entry chunk crossed the 160 kB ceiling by 989 B on the 18-package frontend dependency bump (#567) — see below. |

### 2026-09-06 — 160 kB → 180 kB

The routine weekly frontend group bump (#567: `@sentry/react`, `@tanstack/*`,
`axios`, `katex`, `react-router-dom`, `eslint`, `vite`, and 11 others, all
minor/patch) grew the entry chunk from 158.19 kB to 160.97 kB — **989 B over**
the ceiling, which redded `Frontend (Lint, Types, Tests)` on `qa` and blocked
the deploy.

Protocol step 1 asks whether the growth can be avoided instead. It can't be
lazy-loaded away here: this is not new app code behind a route, it is third-party
bytes spread across a dozen already-imported packages, none individually
responsible for the overage. Splitting another vendor out of the entry chunk was tried
and measured: a `vendor-sentry` `manualChunks` rule moved nothing, because
`@sentry/react` is already dynamically imported behind a DSN check
(`src/shared/observability/reporter.ts`) and so was never in the entry chunk to
begin with. The remaining unsplit packages are individually small.

180 kB restores roughly the headroom the original ceiling was set with (~12% over
measured, versus ~17% at the 2026-06-07 baseline), which is what keeps routine
dependency drift from re-failing CI every few weeks. The runtime side is
unaffected and still independently guarded by the Lighthouse budget (PERF-07).
The next real cut, when someone wants one, is the ~82 kB `hi-*.js` locale chunk
and the 259 kB `vendor-katex` chunk — neither is in the entry chunk, but both are
on the first-load path.
