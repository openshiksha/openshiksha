# SRS Practice Drill Mode

**Date**: 2026-05-21
**Classification**: New
**PR Target**: `feat/2026-05-21-srs-drill` → `modernization`

## Summary

Closes the spaced-repetition loop. Students could already *see* what chapters were due for review via the `DueForReviewPanel`, but the rows were inert. Now tapping **Practice** opens a drill page that pulls up to 5 questions from that chapter, lets the student answer them, and updates the SM-2 schedule based on a server-graded score.

## Legacy Reference

None — legacy OpenShiksha had no spaced repetition system. This builds on the modern `SpacedRepetitionEntry` (SM-2) infrastructure shipped earlier.

## What's New vs. Plan

The plan suggested computing the score on the client and POSTing it raw. We deviated to **server-side grading**:

- `mark_reviewed` accepts `{"answers": {<subpart_id>: <answer>}}` and grades server-side via the existing `core.tasks._grade_subpart` helper.
- This keeps `correct_answer` off the wire (the review endpoint uses `QuestionWithSubpartsStudentSerializer`, consistent with assignment endpoints).
- A `{"score": <float>}` fallback shape is also accepted, so future client surfaces (or tests) can supply a pre-computed score.

This adds two lines of defense:
1. Croupier MCQ shuffling still works (server reverses the shuffle during grading).
2. A student can't open devtools and read off the answers.

## Technical Details

### Backend
- `backend/openshiksha/apps/ai/views.py` — added two actions to `SpacedRepetitionViewSet`:
  - `GET /api/v1/ai/spaced-repetition/{id}/review/` — returns up to 5 random active questions from the entry's chapter via the student-safe serializer.
  - `POST /api/v1/ai/spaced-repetition/{id}/mark-reviewed/` — grades answers server-side (or accepts a raw `score`), applies the SM-2 update inline, returns the refreshed entry plus the computed `score`.
- SM-2 update logic ported directly from the model docstring: success grows interval (1 → 6 → `interval * ef`), failure resets to interval 1 with reps 0.

### Frontend
- `frontend_modern/src/features/student/useSRSDrill.ts` — `useSRSDrill` (GET) and `useMarkReviewed` (POST) hooks.
- `frontend_modern/src/features/student/SRSDrillPage.tsx` — new page with loading, empty, in-progress, and result states. Reuses existing `QuestionCard`.
- `frontend_modern/src/App.tsx` — registered `/student/srs-drill/:entryId` route.
- `frontend_modern/src/features/student/DueForReviewPanel.tsx` — added **Practice** pill button to each row, leading to the drill.

## Tests

**Backend** (`backend/openshiksha/apps/ai/tests/test_srs_drill_api.py`, 11 tests):
- `review` returns chapter questions, caps at 5, hides `correct_answer`, scopes to owning student, handles empty chapters.
- `mark_reviewed` grows interval on success, resets on failure, accepts raw `score`, accepts `answers` (with correct MCQ key after Croupier shuffle) for full credit and partial credit, rejects invalid input, scopes to owning student.

Full backend suite: **306 passed**, up from 291.

Frontend: type-check, lint, build, and vitest suite all clean.

## Migration Notes

No model changes — no migration required.

## Next Steps

- Feed drill scores back into `StudentProficiency` / `StudentMastery` (Phase 2). Right now the drill only nudges SM-2; the broader proficiency pipeline is not touched.
- Move SM-2 update into a model method (`SpacedRepetitionEntry.apply_sm2(score)`) so the same logic can be reused by the existing Celery-side scheduler in `adaptive_analytics.compute_srs_update`.
- Activity Streaks (Priority 2 on today's plan) — deferred to a follow-up PR for atomic review.
