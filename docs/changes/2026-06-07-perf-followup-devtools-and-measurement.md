# Performance Budget — follow-up: prod devtools guard + measurement harness + initiative closeout

**Date:** 2026-06-07
**Initiative:** Performance Budget (close-out)
**Classification:** Improve + docs

## Summary

Three things in one PR, all in service of closing the Performance Budget
initiative cleanly:

1. **Drop `@tanstack/react-query-devtools` from production builds.** `main.tsx`
   now guards the import with `import.meta.env.DEV` behind `React.lazy`, so the
   bundler dead-code-eliminates it from production builds entirely. Dev builds
   still get the devtools (lazy-loaded behind a `<Suspense>`). `vite.config.ts`
   also routes the devtools module to its own `devtools-react-query` chunk so
   it can never accidentally pollute the long-cacheable `vendor-query` chunk
   on a dev build.
2. **Add a repeatable perf measurement harness.**
   `frontend_modern/scripts/measure-perf.mjs` boots Playwright with CDP
   throttling (Slow 4G + 4× CPU, mobile UA), navigates to a URL, and reports
   FCP, total transferred bytes, per-type breakdown, and a per-resource ≥ 5 kB
   table. Run with `node scripts/measure-perf.mjs http://localhost:4173/login`
   against a `npm run preview` build.
3. **Close the initiative.** `docs/initiatives/STATUS.md` and
   `docs/initiatives/performance-budget.md` are flipped to ✅ Done with the
   full ledger of shipped PRs (#251–#255), the measured 855 → 131 kB cut, and
   two documented open follow-ups: the auth-critical-path refactor and the
   deferred PERF-05 (font self-hosting) — both with rationale.
4. **Tiny fix:** `scripts/check-bundle-budget.mjs` had a `#!/usr/bin/env node`
   shebang that Vitest 4 + rolldown can't parse during SSR transform. Removed
   it — the script is invoked via `node scripts/check-bundle-budget.mjs`, not
   executed directly.

## Why no QueryClientProvider refactor?

The PR scoped "move QueryClientProvider below the auth boundary" as a quick
win, but on closer look it requires refactoring `useAuth`,
`useLoginMutation`, `useRegisterMutation`, and `useEnquireMutation` away from
react-query (login/register/enquire all use react-query mutations today). That
is a real ~half-day refactor, not a follow-up tweak. It's documented under §H
"Open follow-ups" in the initiative for whoever picks it up next.

## Why no lazy DOMPurify?

User scoped out. The DOMPurify chunk is only 25 kB and the change is
non-trivial; deferred unless a future measurement promotes it.

## Why no PERF-05 (font self-hosting)?

Real-device measurement (Slow 4G + 4× CPU emulation on `/login`) showed:
- **FCP: 4.6 s** dominated by 415 kB of JS download time.
- **Zero `.woff2` files** fetched in the first-paint window — `font-display: swap`
  pushes the actual font swap past FCP.
- The Google Fonts CSS is 15 kB; full self-hosting would shave ~100–200 ms of
  visible font-swap latency, not first paint.

That's an order of magnitude smaller than what PERF-01..04 already shipped.
Skipping the operational cost of vendoring fonts unless a real LCP trace
promotes it later.

## Verification

- `npm run type-check` / `npm run lint` / `npm test -- --run` (32 files / 203
  tests) / `npm run build` / `npm run check:budget` — all green.
- Production build entry chunk: **129 kB** (under 160 kB ceiling, 31 kB
  headroom).
- No `devtools-react-query` chunk in production `dist/` (proves the DEV guard
  works).
- `scripts/measure-perf.mjs http://localhost:4173/login` against the local
  preview build produces the FCP / per-type / per-resource breakdown above.

## Files

- `frontend_modern/src/main.tsx` — DEV-guarded lazy import for devtools.
- `frontend_modern/vite.config.ts` — `devtools-react-query` chunk isolation.
- `frontend_modern/scripts/measure-perf.mjs` (new) — Playwright + CDP perf
  harness.
- `frontend_modern/scripts/check-bundle-budget.mjs` — drop shebang.
- `docs/initiatives/STATUS.md` — Performance Budget marked Done; Teacher
  Workspace stays #1.
- `docs/initiatives/performance-budget.md` — Status flipped to Done; ledger
  filled with PRs #251–#255 and this PR; §H "Open follow-ups" added.
