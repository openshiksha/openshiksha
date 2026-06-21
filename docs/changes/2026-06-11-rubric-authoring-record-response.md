# Rubric authoring + record-response flow (ASA-7b)

**Date:** 2026-06-11
**Classification:** New (ASA-7 batch anchor, part 2 of 2 — completes ASA-7)
**Initiative:** AI Surface Activation — ASA-7b

## Summary

ASA-7a (#301) shipped the review queue; this PR ships the **input side** of
open-response grading, completing ASA-7 and the last initiative backlog item:

- **Record a response**: the teacher picks a class → student → one of their
  short-answer questions, pastes the student's free-text answer, and the
  server queues AI grading (202 → pending row appears in the queue below).
- **Rubric authoring**: the one rubric a short-answer subpart carries
  (max marks, model answer, optional per-point marking criteria) is created
  and edited inline, right where the teacher records responses — with a nudge
  when a picked question has no rubric ("AI falls back to a rough keyword
  match — add one for fair, transparent marks") and a warning when marking
  points don't sum to the maximum.

First consumer of `/ai/open-rubrics/`. With this, **every `/ai/` endpoint
group has a frontend consumer** — the initiative's North-Star condition.

## Legacy reference

None — legacy had no grading path for free-text answers at all.

## What changed

### Backend (small, justified by a genuinely missing surface)

- `backend/openshiksha/apps/api/views/core.py` — new
  `GET /api/v1/subject-rooms/{id}/students/` action: the room roster
  (`id`, `full_name`, `username`) for teacher pickers. Teacher/admin-only and
  scoped by `get_queryset` (other teachers 404); **students get 404** so they
  cannot enumerate classmates even for rooms they're enrolled in.
- `backend/openshiksha/apps/api/tests/test_core_api.py` — 3 tests
  (`TestSubjectRoomStudentsAction`): teacher sees roster; other teacher 404;
  student 404. No model change, no migration.

### Frontend

- **`useOpenRubrics.ts`** (new) — `OpenResponseRubric`/`RubricCriterion`
  types; `useRubricForSubpart` (resolves the OneToOne to rubric-or-null);
  `useSaveRubric` (POST when none exists, PATCH otherwise);
  `useRoomStudents`; `useShortAnswerSubparts` (teacher's
  `?question_type=short_answer` questions flattened to subpart options);
  `useSubmitOpenResponse` (invalidates all grading-queue views so the
  pending row appears immediately).
- **`RecordResponsePanel.tsx`** (new) — collapsible card mounted at the top
  of `/teacher/grading`: class/student/question selects (student select
  disabled until a class is picked; explanatory copy when the teacher has no
  short-answer questions yet), inline `RubricSection` (summary + Edit, or the
  no-rubric nudge + Add), `RubricForm` (max marks, model answer, add/remove
  marking points, sum-mismatch warning), response textarea, submit → success
  note pointing at the queue. Submit errors surface inline.
- **`OpenResponseGradingPage.tsx`** — mounts the panel above the queue.

## Tests

`RecordResponsePanel.test.tsx` — 7 cases: collapsed-by-default (no fetches);
full record flow posts the submit payload + success note; no-rubric nudge;
rubric create POST; rubric edit PATCH (existing summary shown first);
marking-point sum warning; submit-failure surfaced inline.

Full gates: frontend lint + tsc + **vitest 320/320 (51 files)** + build;
backend **pytest 926 passed, 93.77% coverage**.

## Next steps

ASA backlog is now empty (ASA-1..9 all shipped). Remaining: endpoint-to-
consumer map + DoD audit + initiative close (docs PR).
