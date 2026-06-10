# ASA-2 — Recommendation rows: click-through to chapter practice

**Date**: 2026-06-09
**Classification**: Improve
**Initiative**: AI Surface Activation (ASA-2)

## Summary

"What to Practice Next" rows on the student dashboard were insight without
action: the `ContentRecommendation` payload carries `chapter` (and
`problem_set`), but the panel never used either — students couldn't act on a
recommendation without manually navigating the browse tree. Each row now gets a
"Practice" pill linking straight to chapter practice, closing the
insight→action loop.

## Legacy reference

`focus/` remedial auto-creation embodied the same principle (insight must lead
to action in-flow); no direct legacy UI to port. Routing decision per the daily
plan: link to `/student/browse/chapter/:chapterId` (existing `ProtectedRoute`,
App.tsx:170, valid for `student` and `open_student`; `BrowsePracticePage`
builds a quick-practice session per chapter) rather than the raw problem set.

## What changed

- `frontend_modern/src/features/student/RecommendationsPanel.tsx`
  - Per-row "Practice" pill `Link` to `/student/browse/chapter/${rec.chapter}`,
    styled identically to `DueForReviewPanel`'s Practice pill (rounded-full,
    brand border, hover fill) for cross-panel consistency.
  - Row text stays non-clickable (avoids nested-link a11y traps; keeps
    truncation/layout intact).
  - Score block now hides on <sm screens (same convention as
    `DueForReviewPanel`'s interval block) so the action pill always fits.
- `frontend_modern/src/features/student/RecommendationsPanel.test.tsx`
  - New test: each row exposes a practice link with the correct chapter href.

## Tests

`npx vitest run RecommendationsPanel` — 5 tests passing (1 new, 4 existing
untouched). `npx tsc --noEmit` + `npm run lint` clean.

## Migration notes

None — frontend only.

## Next steps

ASA-3..5 in this batch.
