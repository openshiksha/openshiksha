# M4-07b — Teacher assignment detail → V2

**Classification:** Improve.

## Summary
Migrates `TeacherAssignmentDetailPage` (the class-level per-student
submission/score view) from the legacy `indigo`/`gray-*` template to V2 tokens
+ `src/shared/ui` primitives. Reuses the warm-paper-table treatment from the
Admin classroom-manage page (PR #182).

## Files changed
- `frontend_modern/src/features/teacher/TeacherAssignmentDetailPage.tsx`

## What changed
- Header uses `SectionHeading` with the subject room as the eyebrow and an
  Overdue/Active `Badge` in the action slot.
- KPI block converted to three `Stat` blocks (Due, Submitted, Avg score). The
  Due Stat surfaces an `Overdue` delta pill (`tone="urgent"`) when applicable.
- Submission progress bar gains a `role="progressbar"` with aria attrs.
- Table chrome: warm `ink-100` hairlines, `bg-ink-50` `font-display` header
  row, `brand-50/40` hover rows — matches the Admin table style from #182.
- Status pills → `Badge` (`tone="success"` for submitted, `tone="attention"`
  for pending). Score colours moved from `green/yellow/red-600` to
  `emerald/amber/rose-700`.
- Error and empty states unified through `EmptyState`.
- Hardest Questions panel: warm `os-card` shell, `bg-rose-500` bar on
  `bg-ink-100` track.

## What was preserved
- Data hooks (`useTeacherAssignmentDetail`, `useQuestionMistakes`), routing,
  the `isOverdue`/score-bucket logic, and all callbacks. Pure reskin.

## Continuous improvement
- Adds `role="progressbar"` aria semantics to the submission progress bar.
- Adds focus-visible rings to the Back button and error-state action so they
  are keyboard-discoverable.

## Verification
- `npm run type-check`, `npm run lint`, `npm run build`, `npm test` — all green.
- Grep `primary|indigo|blue-|gray-50|text-gray-` in the file → 0.

## Next
- M4-07c Create-Question authoring page (the densest file in the batch).
