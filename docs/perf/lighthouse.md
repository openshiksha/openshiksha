# Frontend runtime-perf budget — Lighthouse CI (PERF-07)

The [bundle-size budget](budget.md) (PERF-06) guards *static* bytes. It cannot
see what those bytes actually do at runtime: hydration cost, main-thread
blocking, layout shift, time-to-paint. Lighthouse CI fills that gap by running a
throttled-mobile audit on every push and reporting the real metrics.

This matters most for the **Mobile Shell / PWA-Offline** initiative — the whole
point of that work is a fast, installable experience on a mid-range phone, which
is exactly the device class Lighthouse's mobile preset emulates.

## What it audits

| Setting | Value |
| ------- | ----- |
| Route   | `/design` (the only public, backend-free route — same one the e2e smoke trusts) |
| Server  | `vite preview` on `:4173` (the production build, not the dev server) |
| Runs    | 3 (Lighthouse reports the median to damp run-to-run noise) |
| Profile | Lighthouse default: emulated mid-tier mobile + 4× CPU / slow-4G throttling |

Config lives in [`frontend_modern/lighthouserc.json`](../../frontend_modern/lighthouserc.json).
Reports are uploaded to Lighthouse's temporary public storage; the run log
prints a URL where you can open the full report for that commit.

## How CI runs it

The `lighthouse` job in [`.github/workflows/ci-cd.yaml`](../../.github/workflows/ci-cd.yaml)
does `npm ci` → `npm run build` → `npm run lighthouse` (which is
`lhci autorun`). It is **not** in the `build-publish` dependency list, so it
never blocks a deploy.

## Why every assertion is `warn` (for now)

Lighthouse scores are noisy — the same commit can swing several points between
runs depending on the runner's CPU contention. If we gated merges on an `error`
threshold from day one, CI would flake red on green code, and the team would
learn to ignore it. So the job launches as a **visibility tool**:

- Every assertion in `lighthouserc.json` is `warn`. Regressions show up in the
  log and the uploaded report, but don't fail the job.
- The job *does* still fail if collection breaks — e.g. the build won't boot or
  `/design` crashes — so it doubles as a build-smoke check.

## Tighten-to-error protocol

The inverse of the budget's raise-the-ceiling protocol. Once a metric has a
stable baseline worth defending:

1. Watch the `warn` output across a handful of merged PRs and note the metric's
   real spread (min/median/max) on CI.
2. Pick an `error` threshold with comfortable headroom **below** the worst good
   run (for scores) or **above** the worst good run (for `maxNumericValue`
   timings) — enough that normal noise won't trip it.
3. Flip that one line in `lighthouserc.json` from `"warn"` to `"error"` and add
   a row to the **history** section below with the date, the metric, the
   threshold, and the observed baseline that justifies it.
4. Ship the tightening in its own small PR so reviewers see exactly which gate
   went hard and why. Promote one metric at a time.

## Running it locally

```bash
cd frontend_modern
npm run build
npm run lighthouse          # builds the preview server, runs 3 audits, prints a report URL
```

Local numbers run on your unthrottled-relative-to-CI machine, so treat them as
directional. The CI run is the source of truth for the baseline.

## History

| Date       | Change                                                        |
| ---------- | ------------------------------------------------------------- |
| 2026-06-15 | PERF-07 introduced. All assertions `warn`; collecting a baseline before promoting any metric to `error`. |
