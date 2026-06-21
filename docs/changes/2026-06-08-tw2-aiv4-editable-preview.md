# TW-2 / AIV-4 — Editable problem-set preview

**Date:** 2026-06-08
**Initiatives:** Teacher Workspace (TW-2) + Authoring Integrity & Versioning — Phase 2 (AIV-4)
**Classification:** Improve

## Summary

`ProblemSetPreviewPage` gains an **edit mode**: the set's creator toggles "Edit set" and gets per-question Remove + Edit-question affordances and an Add-question entry to the question bank (which already has the Add-to-set sheet). The mode banner switches from brand to amber and surfaces the AIV-3b `EditSafetyBanner` when the set is already in use.

Backend ships the missing `remove-question` endpoint that mirrors `add-question`, plus a regression test pinning the property that makes TW-2 safe: **mutating the live set's question list must not change any pre-existing assignment's `assigned_content` snapshot**. Without AIV-1/2 this would silently rewrite already-assigned work; with them it doesn't, and the test proves it through the API.

## Files

- `backend/openshiksha/apps/api/views/core.py` — `remove-question` action on `ProblemSetViewSet`
- `backend/openshiksha/apps/api/serializers/core.py` — `created_by_me` flag on `ProblemSetSerializer`
- `backend/openshiksha/apps/api/tests/test_problemset_edit_safety.py` (new) — 4 tests
- `frontend_modern/src/features/teacher/useRemoveQuestionFromProblemSet.ts` (new) — mutation hook
- `frontend_modern/src/features/teacher/useProblemSetPreview.ts` — preview type gains `assigned_count`, `has_graded_submissions`, `created_by_me`
- `frontend_modern/src/features/teacher/ProblemSetPreviewPage.tsx` — edit-mode toggle, per-question Remove + Edit, Add-question link, reuses `EditSafetyBanner`
- `frontend_modern/src/features/teacher/ProblemSetPreviewPage.test.tsx` (new) — 5 tests

## Verify

- Backend pytest: 24 passed (`test_problemset_edit_safety.py` + `test_problemset_api.py`).
- Vitest: 9 passed (`ProblemSetPreviewPage.test.tsx` + `EditSafetyBanner.test.tsx`).
- `npm run type-check` clean; `npm run lint` clean (max-warnings 0); `npm run build` clean.

## Notes

- Reorder is deliberately out of scope: `ProblemSet.questions` is an unordered M2M, so reorder would need a through-table or `position` field — a bigger model change that doesn't belong in this atomic PR.
- The "Add question" button sends teachers to the question bank with a `returnTo` query param, reusing the existing `AddToProblemSetSheet` flow that QuestionBankPage already drives.

## Next

- AIV-5 — assignment-level preview rendering from the snapshot + a drift banner when the live set has moved past it.
