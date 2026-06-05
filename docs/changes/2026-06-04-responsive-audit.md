# M5-02 — Per-surface responsive audit (migrated M4 pages)

**Classification:** Fix + audit doc.

## Summary
A focused pass over the V2 surfaces shipped today, looking for layouts that
break at 375px (iPhone SE). Two concrete fixes; the rest of the audit was
clean enough to record as a *clean-bill* note in the ledger.

## Files changed
- `frontend_modern/src/features/student/BrowsePage.tsx` — chapter table can
  now scroll horizontally on viewports narrower than its content.
- `frontend_modern/src/features/teacher/ClassHealthPanel.tsx` — class-health
  table wrapped in an overflow-x scroll container.

## What changed
1. **BrowsePage chapter table.** Was wrapped in `os-card overflow-hidden`,
   which clipped any horizontal overflow. Even though the Subject + Grade
   columns are `hidden sm:table-cell`, the remaining `Chapter / Q / Practice`
   row can still get tight at 375px when a chapter name is long. Switched
   wrapper to `overflow-x-auto` and gave the table a `min-w-[24rem]` floor
   so the column rhythm is preserved instead of squashed.
2. **ClassHealthPanel table.** Four columns at `text-xs` (Chapter / Avg /
   Struggling / Status) fit at 375px in the common case but break with long
   chapter names or wide "X/Y" struggling counts. Wrapped the table in a
   `-mx-1 overflow-x-auto` container with a `min-w-[22rem]` floor on the
   table itself. The `-mx-1` reaches into the dashboard panel's padding so
   the scroll edge doesn't visually float.

## Other surfaces checked (clean, no changes needed)
- **AppShell / Navbar / BottomNav** — covered by M2-02 (#198) and M5-01
  (#195); explicit safe-area-inset top + bottom; hamburger sheet contents
  refactored to be account-only.
- **Student Dashboard, Teacher Dashboard, Parent Dashboard, Admin Dashboard,
  Profile, Proficiency cluster, Assignment detail, SRS drill, Browse-Practice,
  Learning Path** — already `max-w-2xl|3xl|7xl` constrained with
  `px-4 sm:px-6 lg:px-8` and use the `Stat`/`SectionHeading` primitives whose
  `font-display` text scales fluidly. Grid layouts use `grid-cols-1 sm:grid-cols-N`
  patterns throughout.
- **TeacherAssignmentDetailPage** — its submission table is already wrapped
  in `overflow-x-auto`; no change.
- **CreateQuestionPage AI panel** `grid-cols-3` (Type / Difficulty / Count) —
  at 375px each select gets ~95px which fits "MCQ", "Numeric", and the
  digit-only Difficulty/Count cleanly. The widest option, "Multi-select",
  uses a `<select>` whose chevron+option-list is sized to the dropdown popup,
  not the trigger, so visual truncation doesn't happen.
- **EnquirePage** (M3-03 / #199) — composed via `AuthLayout`, which already
  collapses to a single-column paper panel with a `lg:hidden` compact-brand
  block.

## Non-goals
- **Touch-target audit** (44×44 minimum) on student practice — flagged as a
  separate follow-up in the M5-01 change doc; out of scope here.
- **PWA install / offline** — proposed initiative, not part of M5.

## Verification
- `npm run type-check`, `npm run lint`, `npm run build`, `npm test` — all green
  (17 files / 89 tests).
- Grep `primary|indigo|blue-|gray-50|text-gray-` in the touched files → 0.

## Next
M6-01 accessibility audit.
