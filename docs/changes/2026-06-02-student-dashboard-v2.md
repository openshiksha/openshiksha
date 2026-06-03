# 2026-06-02 — Student Dashboard → V2 brand (M4-01)

## Summary
Re-skin `features/student/StudentDashboard.tsx` from the legacy
indigo/gray-50 palette to the V2 "Chalk & Unlock" brand tokens. Closes
**M4-01** of the [V2 design-system initiative](../initiatives/2026-design-system-v2.md).

## Classification
**Improve** — pure visual migration. No data hooks or panel internals touched.

## What changed (token map)
- `text-2xl font-bold text-gray-900` → `font-display text-3xl font-semibold text-ink-900`.
- `text-gray-500` → `text-ink-500`.
- "My Progress" link `text-indigo-600 hover:text-indigo-800` → `text-brand-700 hover:text-brand-800`.
- Open-student "not enrolled" block (`border-indigo-200 bg-indigo-50
  text-indigo-800` + custom `bg-indigo-600` button) → the V2 `EmptyState`
  primitive with a brand `<Button>` CTA.
- Error block kept warm `rose-` palette but switched to `rounded-xl`.

## Scope
Per the daily plan, this PR scopes to the dashboard's own JSX + empty state.
Child panel internals (`DueForReviewPanel`, `RecommendationsPanel`,
`AssignmentList`/`AssignmentCard`, `StreakBadge`, `AnnouncementsBanner`) keep
their existing styling and remain in the M4 backlog as separate increments.

## Token cleanup
`grep -nE "indigo|gray-50|primary-" frontend_modern/src/features/student/StudentDashboard.tsx`
→ no matches.

## Tests
- All 69 existing tests stay green.
- `type-check`, `lint`, `build` clean.

## How to verify
- `npm run dev` → log in as a student → dashboard greeting is `font-display`
  and warm; the "My Progress" link is brand-orange; the empty-state for open
  students renders the keyhole `EmptyState` with a brand CTA.

## Dependency
Depends on PR 1 (Input/Stat/SectionHeading/EmptyState primitives). Branched
off `feat/2026-06-02-ui-primitives`.

## Next
- PR 5 — Teacher Dashboard → V2.
- Follow-up M4 increments: `StreakBadge`, `AssignmentCard`,
  `DueForReviewPanel`, `RecommendationsPanel`, `AnnouncementsBanner` chrome.
