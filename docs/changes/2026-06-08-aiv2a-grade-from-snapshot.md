# AIV-2a — Grade from snapshot

**Date:** 2026-06-08
**Initiative:** Authoring Integrity & Versioning — Phase 1
**Classification:** Improve
**Depends on:** AIV-1 (`Assignment.assigned_content` + snapshot helper)

## Summary

`grade_submission` now reads each subpart's `subpart_type`, `correct_answer`, and `variable_constraints` from `Assignment.assigned_content` instead of the live `QuestionSubpart` row. The live row is still loaded — `Tick.question_subpart` is a real FK that must point somewhere — but the **grading inputs** all come from the frozen snapshot. The legacy live-set path is kept as a defensive fallback for any row the 0023 backfill couldn't reach.

## Golden regression test

`test_grade_against_snapshot_ignores_live_answer_edit` is the proof: snapshot the assignment, edit the live `correct_answer` to a wrong value, submit the original right answer, re-grade ⇒ **score is still 1.0**. Without AIV-2a this test fails — the student who was correct becomes wrong on re-grade.

Companion: `test_new_assignment_after_live_edit_uses_new_answer` confirms snapshots are per-assignment, not global — a new assignment created *after* the edit grades against the new answer.

## Files

- `backend/openshiksha/apps/core/tasks.py` — `grade_submission` snapshot branch + defensive live-set fallback
- `backend/openshiksha/apps/core/tests/test_grading_tasks.py` — 3 new tests:
  - `test_grade_uses_snapshot_when_present` — happy path
  - `test_grade_against_snapshot_ignores_live_answer_edit` — **GOLDEN**
  - `test_new_assignment_after_live_edit_uses_new_answer` — corollary

## Verify

- pytest: 38 passed (grading + remedial + AIV-1 snapshots tests)
- `manage.py check` clean

## Next

- AIV-2b — student assignment-detail serializer renders from the snapshot
- AIV-3a — `assigned_count` + `has_graded_submissions` flags
