# M5-01 — Mobile bottom tab bar

**Classification:** New.

## Summary
Adds a persistent **bottom tab bar** on mobile (`<sm`) so the primary
navigation is always within thumb reach. Tabs are role-aware:

- **Student / Open student** — Home · Browse · Path · Profile
- **Teacher** — Home · Questions · Profile
- **Parent** — Home · Profile
- **Admin** — School · Profile

On `sm:` and above the bottom bar is hidden and the existing Navbar links
take over.

## Files changed
- `frontend_modern/src/features/layout/BottomNav.tsx` — new component
  (~170 LOC), inline SVG icons, role-aware tab list, prefix-match for
  highlighting nested routes (e.g. `/student/browse/chapter/42` highlights
  Browse), `aria-current="page"` on the active tab, `aria-label="Primary"` on
  the `<nav>`, focus-visible brand ring.
- `frontend_modern/src/features/layout/AppShell.tsx` — render `<BottomNav />`
  and add `pb-24 sm:pb-8` on `<main>` so page content clears the bar on
  mobile.
- `frontend_modern/src/features/layout/BottomNav.test.tsx` — 5 unit tests
  covering: unauth render-nothing; STUDENT tab set; prefix-match highlight on
  a nested route; TEACHER tab set; OPEN_STUDENT identical to STUDENT.

## Why this matters
The legacy hamburger menu hides the primary nav behind a tap. With a bottom
tab bar, switching between Home / Browse / Path costs one thumb tap — the
table-stakes feel for an app a teenager uses every day. The hamburger menu
is kept for secondary actions (Profile, Sign out, the rare "Proficiency"
deep-link).

## Design notes
- Surface: `bg-white/95 backdrop-blur` over a `border-t border-ink-100`.
  Sits above `env(safe-area-inset-bottom)` so it clears the iOS home
  indicator.
- Active tab: `text-brand-700`; inactive: `text-ink-500` with hover lift.
- One primary action per surface still holds — the active tab is the only
  brand-orange element on the strip.

## Verification
- `npm run type-check`, `npm run lint`, `npm run build` — green.
- `npm test` — 17 files / 89 tests pass (was 84; +5 from this PR).

## Next
- M2-02 mobile nav polish — consider replacing the hamburger entirely if the
  bottom bar covers everything users actually reach.
- M5-02 — touch-target audit (44×44 minimum) on student practice pages.
