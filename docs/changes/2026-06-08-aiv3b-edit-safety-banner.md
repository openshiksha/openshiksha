# AIV-3b — Edit-safety banner in teacher UI

**Date:** 2026-06-08
**Initiative:** Authoring Integrity & Versioning — Phase 1
**Classification:** Improve
**Depends on:** AIV-3a (`assigned_count` + `has_graded_submissions` serializer flags)

## Summary

Adds a non-blocking, informational banner to the teacher question-edit form (`CreateQuestionPage` in edit mode). When the question being edited is already referenced by one or more assignments, the banner says so and explains:

> Your edits apply to **future** assignments only — existing ones keep exactly what students were given.

Stronger wording when at least one submission has been graded: "…and were graded against."

Editing is **safe by construction** (AIV-1/2 snapshot per-assignment content), so this banner is purely advisory — nothing is disabled.

## Files

- `frontend_modern/src/types/index.ts` — `assigned_count?` and `has_graded_submissions?` on `Question` and `ProblemSet`
- `frontend_modern/src/features/teacher/EditSafetyBanner.tsx` (new)
- `frontend_modern/src/features/teacher/EditSafetyBanner.test.tsx` (new) — 4 tests
- `frontend_modern/src/features/teacher/CreateQuestionPage.tsx` — render the banner in edit mode

## Verify

- `npm run type-check` clean
- `npm run lint` clean (max-warnings 0)
- `npm run build` clean
- Vitest: 4 passed

## Notes

- ProblemSet edit surface uses the same `EditSafetyBanner` component (noun="this problem set") — wiring will happen alongside the editable-preview work (TW-2) so we don't add a banner to a page that doesn't yet permit edits.
