# M7-03 (final slice) — Question Bank chapter filter UI

**Classification:** Improve.

## Summary
Closes the remaining M7-03 UI gap: the QuestionBank backend already supported
`?chapter=<id>` but the filter bar didn't expose it. Adds a third **Chapter**
`<Select>` scoped to the currently-selected subject.

## Files changed
- `frontend_modern/src/features/teacher/QuestionBankPage.tsx`

## What changed
- Imports `useChapters` (already in the codebase; scoped to a subject).
- New `selectedChapter` state, wired into `useQuestionList` as the
  `chapter` filter param. `hasFilters` and `clearFilters` updated to
  include it.
- New `<Select>` rendered below the Subject/Difficulty row. Disabled until a
  subject is picked (with `hint="Pick a subject first"` for discoverability)
  — a chapter belongs to a subject, so listing every chapter across every
  subject is overwhelming.
- Subject change drops the chapter selection so we never filter against a
  stale chapter id.

## What was preserved
- All existing search/subject/difficulty wiring; the focused-question
  reconciliation; the AddToProblemSet sheet behaviour.

## Verification
- `npm run type-check`, `npm run lint`, `npm run build`, `npm test` — all
  green (17 / 89).
- Backend already supports `?chapter=<id>` (see `QuestionViewSet.get_queryset`
  in `views/core.py`); no new tests required.

## Next
M6-03 visual-regression baseline activation. Then the V2 initiative is done.
