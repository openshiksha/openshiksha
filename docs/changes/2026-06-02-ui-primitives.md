# 2026-06-02 — `ui/` foundation primitives (M1-06)

## Summary
Add the four remaining V2 "Chalk & Unlock" foundation primitives — `Input`
(+ `Textarea`, `Select`), `Stat`, `SectionHeading`, `EmptyState` — to
`frontend_modern/src/shared/ui/`. Closes **M1-06** of the
[V2 design system initiative](../initiatives/2026-design-system-v2.md).

## Classification
**New** — additive only, no existing pages touched.

## Why
The brand shell, login, and home page already speak V2 — but every M4 dashboard
migration still needs primitives that don't exist yet. Building these as a
foundation PR means later page migrations compose `ui/` parts instead of
hand-rolling warm styles. PR 3/4/5 in today's batch consume the same primitives.

## What's new
- `Input` — labelled text field, with `hint`, `error`, `leftIcon`, ARIA wiring
  (`aria-invalid` + `aria-describedby`), focus-visible ring, disabled state.
- `Textarea` — same chrome as `Input`, multiline.
- `Select` — native select with brand chevron and matching label/hint/error chrome.
- `Stat` — KPI block for dashboard headlines: big `font-display` value, small
  uppercase label, optional `delta` pill (consumes `Badge` tones) + `hint`.
- `SectionHeading` — `font-display` section title with optional `eyebrow`,
  `description`, and right-aligned `action` slot. `as` prop sets semantic level.
- `EmptyState` — canonical "nothing here yet" surface on `.os-card`, brand
  keyhole glyph, optional action.

## Wiring
- Exported from `src/shared/ui/index.ts`.
- Every new primitive rendered on the `/design` route with all key variants
  (Input default/error/disabled, Select, Textarea, Stat with/without delta,
  SectionHeading with/without action, EmptyState with/without action).
- `shared/ui/README.md` table updated.

## Tests
- `Input.test.tsx`, `Stat.test.tsx`, `SectionHeading.test.tsx`,
  `EmptyState.test.tsx` — render-smoke per primitive (default + key variants).
- All frontend tests green: 40/40.
- `npm run type-check`, `npm run lint`, `npm run build` clean.

## Next steps
- PR 2 — global states (LoadingSpinner, NotFoundPage, ErrorBoundary).
- PR 3 — register flow → V2 (uses new `Input`).
- PR 4 — Student Dashboard → V2 (uses `Stat`, `SectionHeading`, `EmptyState`).
- PR 5 — Teacher Dashboard → V2 (same primitives).
