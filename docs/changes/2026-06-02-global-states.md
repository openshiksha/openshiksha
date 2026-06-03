# 2026-06-02 — Global states: branded spinner, 404, error boundary (M2-03)

## Summary
Replace the legacy indigo spinner / plain-text 404 / missing error-recovery surface
with branded V2 equivalents. Closes **M2-03** of the
[V2 design-system initiative](../initiatives/2026-design-system-v2.md).

## Classification
**New** + **Improve** — re-brand existing `LoadingSpinner` chrome, add new
`ErrorBoundary` and `NotFoundPage`, wire both into `App.tsx`.

## What changed
- `src/shared/components/LoadingSpinner.tsx` — repainted from `border-indigo-600` to
  a `brand-100` track + `brand-600` head, sizes use `border-2`/`border-[3px]`
  rings instead of a single bottom-border arc. Uses `motion-safe:animate-spin`
  so `prefers-reduced-motion` users see a static ring.
- `src/shared/ui/LoadingSpinner.tsx` — canonical V2 re-export so new code imports
  from `@/shared/ui`.
- `src/shared/ui/ErrorBoundary.tsx` — class-component fallback with warm `.os-card`
  recovery surface, rose alert icon, "Try again" CTA, optional custom `fallback`.
- `src/features/shared/NotFoundPage.tsx` — warm-paper 404 with `Logo`, big
  `font-display` "404", calm copy, "Back to home" CTA.
- `src/App.tsx` — replaced inline `NotFound` with `NotFoundPage`; wrapped
  `<Routes>` in `<ErrorBoundary>` so render-time errors anywhere under the
  router fall back gracefully without swallowing auth redirects.
- `/design` route gained "Loading spinner" and "404 / error boundary" preview
  sections.

## Why
Any route can hit a full-screen unbranded state (spinner / 404 / crash) and
break the brand. This PR makes all three on-brand without introducing a toast
dependency (`react-hot-toast` not present today — left as a follow-up per the
plan).

## Tests
- `ErrorBoundary.test.tsx` — renders children when no error; renders default
  fallback when child throws; supports custom `fallback`.
- `NotFoundPage.test.tsx` — renders "404", headline, and a "Back to home" link
  targeting `/`.
- Frontend: `npm run type-check`, `npm run lint`, `npm run build`,
  `npm test` — all green (58/58).

## How to verify
- `cd frontend_modern && npm run dev`. Visit `/design` and scroll to "Loading
  spinner" + "404 / error boundary" sections.
- Visit `/this-route-does-not-exist` → branded 404 with keyhole logo and back-home link.
- Toggle OS reduced-motion → the spinner becomes a static ring.

## Next
- PR 3 — register flow → V2 (uses new `Input` from PR 1).
- PR 4 — Student Dashboard → V2.
- PR 5 — Teacher Dashboard → V2.
- Follow-up: theme `react-hot-toast` once / if it's introduced.
