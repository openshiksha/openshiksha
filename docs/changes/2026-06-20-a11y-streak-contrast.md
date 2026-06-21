# 2026-06-20 — A11Y-7: StreakBadge secondary-label contrast

## Summary
Fixes the one student-core-loop colour-contrast finding the A11Y-6 axe inventory
surfaced that isn't covered by A11Y-4: the `StreakBadge` secondary labels were
de-emphasised with `opacity-70` / `opacity-60`, which dropped the tinted text
below the WCAG AA 4.5 : 1 bar against the badge fill.

## Classification
**Improve** — frontend-only, one component. No API/schema change.

## What changed
- `src/features/student/StreakBadge.tsx`: removed `opacity-70` / `opacity-60`
  from the three secondary `<span>`s (tier label, "best", grace note). They stay
  de-emphasised by **weight** (`font-normal` vs the badge's `font-semibold`),
  which carries the hierarchy without lowering contrast. The tier `textColor`
  tokens already clear AA on their own fill at full opacity.

## Why this was the finding
The `StreakBadge` renders in the shared app chrome, so its labels appeared on
every authenticated route's axe report. Measured (A11Y-6):
`opacity-70` → 3.6 : 1, `opacity-60` → 2.9 : 1 (tinted text on the amber/brand
badge fill). Removing the overlay restores the tokens' native AA-passing ratios.

## Legacy reference
None — net-new.

## Tests / how to verify
- `npm run type-check` + `npm run lint` — green.
- `npx playwright test a11y` (with the A11Y-6 harness): the student-route
  `color-contrast` blocking node count drops from 4 → 2 — the two remaining
  (`.btn-brand`, small `text-brand-700`) are resolved by A11Y-4
  ([#417](https://github.com/openshiksha/openshiksha/pull/417)).

## Next steps
A11Y-8: once A11Y-4 (#417) and this PR are merged to `modernization` and the
student routes compute zero blocking, flip them to `gate: true` in
`e2e/a11y.spec.ts`. (Gating before then would red-wall CI on the still-present
brand contrast.)
