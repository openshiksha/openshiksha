# SRS drill result screen — per-subpart AI explanations (ASA-8)

**Date:** 2026-06-10
**Classification:** Improve
**Initiative:** AI Surface Activation — ASA-8 (daily plan 2026-06-10 PR 4)

## Summary

After a scored SRS drill round the student used to see only a score card —
right/wrong with no way to learn *why*, which is exactly the moment
`/ai/explanations/` exists for. Both drill result screens (review and
practice) now render the answered questions read-only below the result card,
which unlocks the same per-subpart "✨ Explain this answer" affordance that
assignments got in ASA-4 (#288). Initiative principle 5: an insight you can't
act on is half-shipped.

## Legacy reference

None — SRS is a modern addition; legacy students saw only marks, never
explanations (fixed for assignments in ASA-4).

## What changed

- `frontend_modern/src/features/student/SRSDrillPage.tsx`
  - New `renderAnswerReview(explanationScore)` section: "Go over your
    answers" heading + the drill's `QuestionCard`s with `isSubmitted` and
    `explanationScore`, appended to both the review-result and
    practice-result screens.
  - Reuses `QuestionCard`'s existing ASA-4 wiring — `explanationScore`
    enables `ExplanationPanel` per subpart (collapsed by default; on expand
    it generates via 202 → polls → renders with the `✨ AI-generated` /
    `Auto-explanation` provenance label). Students also get the worked
    solution reveal for free, since `QuestionCard` shows it when submitted.
  - Review round passes the graded `result.score` (ASA-4's conservative
    derivation: correct framing only on a perfect score). Practice rounds
    are never graded client-side, so they pass `null` — the affordance still
    works (generation is per subpart, not per submission) with the
    "where this went wrong" framing.
- `frontend_modern/src/features/student/SRSDrillPage.test.tsx`
  - QuestionCard mock now surfaces `isSubmitted`/`explanationScore`; 3 new
    tests: no answer review mid-drill; review result passes the graded score;
    practice result passes `null`.

No new hooks, no backend change. `ExplanationPanel` stays inside the student
chunk (no bundle change).

## Tests

`npx vitest run SRSDrillPage` — 6 passed (3 existing repeat-guard tests
untouched, 3 new). The generate → poll → explanation / error+retry flows are
covered by `ExplanationPanel.test.tsx` (ASA-4); the new tests assert the
page-level wiring boundary rather than duplicating that coverage.

## Next steps

ASA-6 (assignment draft builder) is the batch anchor, next in this run.
