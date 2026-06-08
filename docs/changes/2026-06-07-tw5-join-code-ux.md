# TW-5 — Join-code UX

**Classification:** Improve (frontend-only).
**Initiative:** Teacher Workspace.
**Branch:** `feat/2026-06-07-tw5-join-code-ux`.

## Summary

`ClassroomCodeWidget` now surfaces the join code's expiry, a copyable shareable
link (`/register/school?code=…`), and a confirmation step before regenerating
(regenerate invalidates the existing code, so this prevents a slip from cutting
off students who already have it). `RegisterSchoolPage` reads `?code=` from the
query string and prefills the join-code field.

## Why

The backend already serializes `expires_at` and supports regeneration, but the
UI hid both. Per the initiative's "no dead-ends" principle, the share path now
ends in a link a teacher can paste into chat / WhatsApp.

## Changes

- `frontend_modern/src/features/teacher/ClassroomCodeWidget.tsx` — expiry chip
  (urgent < 48 h), share-link row with copy, two-step regenerate confirm.
- `frontend_modern/src/features/auth/RegisterSchoolPage.tsx` — read `?code=`
  from `useSearchParams`, uppercase + truncate to 8 chars, prefill state.
- `frontend_modern/src/features/teacher/ClassroomCodeWidget.test.tsx` — 7 tests.

## Verify

- `npx vitest run src/features/teacher/ClassroomCodeWidget.test.tsx` — 7/7 green.
- `npm run type-check` clean. `npm run build` + `npm run check:budget` —
  entry chunk 93.05 kB (160 kB budget).

## Next

TW-4 (dashboard needs-attention) and TW-3 (assignment lifecycle) follow in this
batch.
