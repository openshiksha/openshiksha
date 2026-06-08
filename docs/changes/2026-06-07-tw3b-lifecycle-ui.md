# TW-3b — Assignment lifecycle UI (frontend)

**Classification:** Improve (frontend, depends on TW-3a).
**Initiative:** Teacher Workspace.
**Branch:** `feat/2026-06-07-tw3b-lifecycle-ui` (branched off TW-3a).

## Summary

Adds inline lifecycle controls to `TeacherAssignmentDetailPage`:
- A `datetime-local` due-date editor that PATCHes the assignment (already
  permitted by the `ModelViewSet`).
- Close / Reopen buttons wired to the TW-3a `close` / `reopen` actions.
- Header badge swaps among `Active` / `Overdue` / `Closed` from the serialized
  `status`.
- Due-date input and Save button disabled while the assignment is closed
  (re-date by reopening first).

After a successful mutation, the detail and list queries are invalidated so
the dashboard's `NeedsAttentionPanel` reflects the change.

## Why

`TeacherAssignmentDetailPage` was read-only — a teacher who set the wrong due
date or wanted to stop accepting late work had to use Django admin. This is
the TW-3 Definition of Done.

## Changes

- `frontend_modern/src/features/teacher/useTeacherAssignmentDetail.ts` —
  add `updateDueAtMutation`, `closeMutation`, `reopenMutation`; invalidate
  detail + list queries on success.
- `frontend_modern/src/features/teacher/TeacherAssignmentDetailPage.tsx` —
  render lifecycle controls, derive status badge.
- `frontend_modern/src/features/teacher/TeacherAssignmentDetailPage.test.tsx`
  — 6 tests: badges (Active/Closed), PATCH due-date, POST close/reopen,
  disabled-when-closed.

## Verify

- `npm run lint` clean, `npm run type-check` clean.
- `npx vitest run …TeacherAssignmentDetailPage.test.tsx` — 6/6 green.
- `npm run build` + `npm run check:budget` — entry 92.99 kB / 160 kB.

## Next

TW-T (Playwright e2e) locks in the full TW-1 → TW-3 continuity flow.
