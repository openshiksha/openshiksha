# AIV-2b — Serve snapshot to student

**Date:** 2026-06-08
**Initiative:** Authoring Integrity & Versioning — Phase 1
**Classification:** Improve
**Depends on:** AIV-1 (`Assignment.assigned_content` + snapshot helper)

## Summary

`AssignmentDetailSerializer` (the student assignment-detail endpoint) now renders the embedded problem-set's `questions` array from `Assignment.assigned_content` when it's populated. Per-student MCQ option shuffle and `{{var}}` substitution still flow through the same croupier helpers — only the **source** of the questions, options, prompts, widget configs, hints, and solutions moves from the live DB rows to the frozen snapshot.

Response shape is preserved 1:1 with the live path; the frontend doesn't change.

## Files

- `core/snapshots.py` — new `render_snapshot_for_student(snapshot, *, student_id, include_solutions)` helper that applies the student-safe transformations to a snapshot's questions.
- `api/serializers/core.py` — `AssignmentDetailSerializer.to_representation` swaps `problem_set.questions` for the snapshot-rendered list when `assigned_content` is present.
- `api/tests/test_assignment_snapshot_view.py` (new) — 4 tests:
  - Student sees the snapshot prompt, not a live-edited prompt.
  - Response never leaks `correct_answer`.
  - Response shape parity — widget fields always present.
  - Question removed from the live set ⇒ student still sees the snapshot.

## Verify

- pytest: 24 passed (assignment API + snapshot view tests).
- Shape regression covered by the existing `test_assignment_api.py` tests that assert response keys.

## Next

- AIV-3a — `assigned_count` + `has_graded_submissions` read flags
- AIV-3b — edit-safety notice in teacher UI
