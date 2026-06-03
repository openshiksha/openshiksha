# 2026-06-02 — Teacher Dashboard → V2 brand (M4-03)

## Summary
Re-skin `features/teacher/TeacherDashboard.tsx` (and its `AssignmentRow`
internal sub-component) from indigo/gray to V2 brand+ink tokens. Closes
**M4-03** of the [V2 design-system initiative](../initiatives/2026-design-system-v2.md).

## Classification
**Improve** — pure visual migration. Data hooks (`useSubjectRooms`,
`useTeacherAssignments`) and panel internals (`ClassHealthPanel`,
`WeeklyReportPanel`, `InterventionsPanel`, `ClassroomCodeWidget`) are untouched.

## What changed
- Headline → `font-display` `text-ink-900`; body copy → `text-ink-500`.
- 3 action buttons (`+ New question`, `+ Problem set`, `+ New assignment`)
  now compose the `<Button>` primitive — first two as `variant="ghost"`,
  the last as the brand "unlock" action.
- Added a 3-up headline `Stat` block (Subject rooms / Students / Open
  assignments) using the new `Stat` primitive — only renders when at least
  one subject room exists.
- Section headers ("Subject rooms", "Assignments") now use `SectionHeading`.
- Empty states ("No subject rooms yet", "No assignments yet") now use the
  `EmptyState` primitive — the second has a brand `<Button>` CTA.
- `AssignmentRow` repainted: `border-indigo-300` hover → `border-brand-300`;
  progress bar `bg-indigo-500` → `bg-brand-500`; legacy `bg-gray-100`/`text-gray-*`
  → `bg-ink-100`/`text-ink-*`. Now a `<button>` for keyboard activation +
  `focus-visible` ring.
- Subject-room cards switched from raw `bg-white border-gray-200` to `<Card>`.

## Scope
Per the daily plan, this PR is the dashboard host + its inline `AssignmentRow`
only. The four child panels (`ClassHealthPanel`, `WeeklyReportPanel`,
`InterventionsPanel`, `ClassroomCodeWidget`) keep their internal styling and
remain in the M4 backlog as separate increments.

## Token cleanup
`grep -nE "indigo|gray-50|primary-" frontend_modern/src/features/teacher/TeacherDashboard.tsx`
→ no matches.

## Tests
- All 69 existing tests stay green.
- `type-check`, `lint`, `build` clean.

## How to verify
- `npm run dev` → log in as a teacher → dashboard headline is `font-display`;
  action buttons use brand chrome; stat block shows totals; empty states
  render the keyhole `EmptyState`; assignment rows have brand progress bars.

## Dependency
Depends on PR 1 (Stat / SectionHeading / EmptyState primitives). Branched off
`feat/2026-06-02-ui-primitives`.

## Next
- Migrate `ClassHealthPanel`, `WeeklyReportPanel`, `InterventionsPanel`
  panel chrome (M4 follow-up).
- M4-02 Parent Dashboard, M4-04 Admin, M4-05 Assignment detail + SRS, etc.
