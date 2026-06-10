# ASA-1 — DueForReviewPanel: loading skeleton + explanatory empty state

**Date**: 2026-06-09
**Classification**: Improve
**Initiative**: AI Surface Activation (ASA-1)

## Summary

`DueForReviewPanel` on the student dashboard rendered `null` until the SRS
due-entries fetch resolved, then popped in and shoved the dashboard layout. It
also disappeared silently when a student had nothing due, leaving no hint that
a review schedule exists. This applies the exact state-handling pattern shipped
for `RecommendationsPanel` in #283 to its sibling panel.

## Legacy reference

None — spaced repetition has no legacy equivalent (modern-only feature, SM-2
engine in `backend/openshiksha/apps/ai/`). The pattern reference is internal:
`RecommendationsPanel.tsx` as polished in PR #283.

## What changed

- `frontend_modern/src/features/student/DueForReviewPanel.tsx`
  - Destructured `isLoading` / `isError` from `useSpacedRepetitionDue()` (the
    hook already exposed them via React Query).
  - Loading: shape-matched skeleton card (header + 3 rows with dot, two text
    lines, pill-shaped action placeholder) inside the same
    `os-card border-amber-200 p-5 mt-6` footprint so the layout doesn't reflow
    on resolve.
  - Empty: compact explanatory card — "Due for Review" heading + "Nothing due
    yet — finish a few assignments and your review schedule will appear here."
  - Error: panel returns `null` with the same explanatory comment used in
    `RecommendationsPanel` (dashboard already surfaces connectivity errors).
- `frontend_modern/src/features/student/DueForReviewPanel.test.tsx` (new)

## Tests

`npx vitest run DueForReviewPanel` — 4 tests, all passing:
1. Skeleton renders while loading (no pop-in).
2. Populated render: urgency labels, overdue badge, sorted practice links.
3. Empty state shows the explanatory copy.
4. Panel hides entirely on fetch error.

Also: `npx tsc --noEmit` and `npm run lint` clean.

## Migration notes

None — frontend only.

## Next steps

ASA-2..5 in this batch (recommendation click-through, SRS repeat-review guard,
answer explanations, misconception clusters panel).
