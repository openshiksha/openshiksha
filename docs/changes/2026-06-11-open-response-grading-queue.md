# Open-response grading queue — first consumer of /ai/open-grades/ (ASA-7a)

**Date:** 2026-06-11
**Classification:** New (ASA-7 batch anchor, part 1 of 2)
**Initiative:** AI Surface Activation — ASA-7a

## Summary

`/ai/open-grades/` was the last fully-built, tested `/ai/` endpoint group with
zero frontend consumers. This PR wires its review surface: a teacher
`AI grading` page (`/teacher/grading`) where free-text answers get an
AI-suggested score, plain-language feedback, and a per-criterion breakdown —
and the teacher finalises every one (accept in one click or override with
their own marks + comment). The AI never finalises anything. With this, **all
4 dark endpoint groups are lit**; ASA-7b (rubric authoring + record-response)
completes the loop in the next PR.

## Legacy reference

Legacy `grader/` auto-graded MCQ/numeric only; free-text questions had no
grading path at all (modern core pipeline grades short answers to 0). This is
a New capability with the teacher kept firmly in the loop.

## What changed

- **`frontend_modern/src/features/teacher/useOpenResponseGrading.ts`** (new) —
  `OpenResponseGrade` type mirroring `OpenResponseGradeSerializer`;
  `useOpenGrades({subjectRoomId?, status?})` list query (array/`{results}`
  tolerant) polling every 3 s **only while a row is pending**;
  `useReviewOpenGrade` / `useRegradeOpenGrade` mutations invalidating all
  open-grades lists; `gradeErrorDetail()` for axios-shaped 400/409 details.
- **`frontend_modern/src/features/teacher/OpenResponseGradingPage.tsx`** (new) —
  - Filters: class select (`useSubjectRooms`) + status chips (All / Needs
    review / AI grading / Finalised / Failed).
  - **ai_graded card**: student, question, quoted response, "AI suggests
    X/Y" + confidence + `AIBadge` (`Auto-graded` + extra-care note on the
    stub path — the heuristic keyword match deserves a stronger caveat than
    other stub surfaces), criterion rows, review form (score defaults to the
    suggestion → "Accept suggestion" is one click; typing a different score
    relabels to "Save final grade"), "Ask AI again" (regrade).
  - **pending**: pulsing working state (polling flips it). **failed**:
    `error_detail` + retry. **reviewed**: final grade, override note when the
    teacher changed the AI's score, teacher comment.
  - List-error → error + Retry (never the empty state); loading →
    shape-matched skeletons; empty → explanatory `EmptyState` (separate copy
    when filters are active).
- **`frontend_modern/src/App.tsx`** — lazy route `/teacher/grading`.
- **`frontend_modern/src/features/teacher/TeacherDashboard.tsx`** —
  "✨ AI grading" ghost button in the dashboard header.

## Backend

None — `OpenResponseGradeViewSet` was complete, teacher-scoped and tested
(`test_open_response_grading.py`, 20 tests).

## Tests

`OpenResponseGradingPage.test.tsx` — 10 cases: skeleton-not-empty; ai_graded
card render (suggestion, confidence, criteria, provenance); accept-suggestion
posts suggested score; override posts score + comment; pending + failed
affordances; reviewed card with override note; stub Auto-graded + care note;
status-chip re-query; list-error + Retry recovery; explanatory empty state.

Full gate: lint, tsc, **vitest 313/313 (50 files)**, build — all green.

## Notes

Stacked on #300 (AIBadge) which is stacked on #299 — merge in order
#299 → #300 → this, retargeting each to `modernization` before merging.

## Next steps

ASA-7b: rubric authoring (max marks, model answer, criteria) + the
"record a response" entry point on this page.
