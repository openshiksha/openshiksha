# 2026-06-23 — A11Y-11: brand-text-on-tint contrast remediation

## Summary
Fixes the one blocking `color-contrast` finding the A11Y-9 teacher/parent axe
baseline surfaced on `/parent`: small **`brand-700` text on a `brand-50` tint** is
only **4.45 : 1** — a hair under WCAG AA's 4.5 : 1. A11Y-4 verified `brand-700`
(`#C05300`) against pure white (≥ 4.5 : 1) but not against the warm `brand-50`
(`#FFF8F1`) tint. The fix moves small brand text on a brand tint to **`brand-800`**
(`#9E4500`, ≥ 4.5 : 1) and documents the rule. This unblocks gating `/parent` in
the Batch-3 close-out.

## Classification
**Improve** — frontend-only token-usage fix + design-doc rule. No API/schema change.

## What changed
- `src/features/parent/ParentDashboard.tsx`: the "View insights" link
  (`text-sm font-semibold` on `bg-brand-50`) → `text-brand-700` → **`text-brand-800`**
  (the axe-flagged node).
- `src/features/student/AssignmentList.tsx`: the `brand` section-count badge accent
  (`text-xs` on `bg-brand-50`) → `text-brand-700` → **`text-brand-800`**. Same
  latent pattern; rendered conditionally so axe hadn't caught it on the gated
  student routes, but it fails identically.
- `docs/initiatives/2026-design-system-v2.md`: corrected the `brand-700` token row
  (it clears AA on white/the page background, **not** on the `brand-50/100` tint)
  and added a contrast rule: *small brand text on a `brand-50`/`brand-100` tint uses
  `brand-800`.*

## Scope notes (what was deliberately left)
- `QuestionCard.tsx` toggle button: `text-brand-700` with **no background** — it
  renders on the white `.os-card`, where `#C05300` ≈ 4.6 : 1 (passes); the brand-50
  panel below it carries `text-ink-800`, not brand text. Unchanged.
- `CreateAssignmentPage.tsx` due-date icon circle: `bg-brand-50 text-brand-700`
  colours an **SVG icon** (non-text → 3 : 1 bar, 4.45 passes). Unchanged.

## Tests
- `npx playwright test a11y` — 15 passed; `/parent` `blocking: []` (was one
  `color-contrast` node).
- `npx tsc --noEmit`, `eslint --max-warnings 0`, and the `AssignmentList` +
  `ParentDashboard` Vitest suites (9 tests) all pass.

## Migration notes
None.

## Next steps
- **A11Y-12** — gate the now-clean teacher + parent routes + Batch 3 close-out.
