# AIV-1 — Assignment content snapshots

**Date:** 2026-06-08
**Initiative:** Authoring Integrity & Versioning — Phase 1
**Classification:** New (foundation, zero behaviour change)

## Summary

Add `Assignment.assigned_content` JSONField + `apps.core.snapshots.build_assignment_snapshot()` helper. Capture a frozen copy of the problem set's questions at assign time in both creation paths (`AssignmentSerializer.create` and `_create_remedial_assignment`). Backfill every existing assignment from its live set in a data migration.

This is the foundation for AIV-2a (grade from snapshot) and AIV-2b (serve to student). On its own it changes no behaviour — readers still hit the live set in this PR — but it makes the snapshot available everywhere it'll be needed next.

## Why

`grade_submission` reads the live `ProblemSet` + live `QuestionSubpart.correct_answer`. Editing a question or swapping questions on a problem set therefore retroactively re-grades work that was already assigned. The fix is copy-on-assign: freeze the content the moment we assign it.

## Files

- `backend/openshiksha/apps/core/models.py` — `Assignment.assigned_content = JSONField(null=True, blank=True)`
- `backend/openshiksha/apps/core/snapshots.py` (new) — `build_assignment_snapshot(problem_set)` + `iter_snapshot_subparts(snapshot)`; `SNAPSHOT_SCHEMA_VERSION = 1`
- `backend/openshiksha/apps/core/migrations/0022_assignment_assigned_content.py` — schema
- `backend/openshiksha/apps/core/migrations/0023_backfill_assigned_content.py` — data migration, idempotent
- `backend/openshiksha/apps/api/serializers/core.py` — capture in `AssignmentSerializer.create`
- `backend/openshiksha/apps/core/tasks.py` — capture in `_create_remedial_assignment`
- `backend/openshiksha/apps/core/tests/test_snapshots.py` (new) — shape, both capture paths, byte-identical-after-live-edit

## Snapshot shape

```
{
  "schema_version": 1,
  "captured_at": "<iso8601>",
  "problem_set_id": int,
  "problem_set_title": str,
  "questions": [
    {
      "question_id": int, "question_type": str, "difficulty": int, "stem_text": str,
      "subparts": [
        { "subpart_id": int, "index": int, "subpart_type": str,
          "question_text": str, "options": ..., "correct_answer": ...,
          "variable_constraints": ..., "image_url": str,
          "solution_text": str, "hint_text": str,
          "widget_kind": str, "widget_config": ...,
          "interactive_html": str, "is_interactive": bool }
      ]
    }
  ]
}
```

`subpart_id` is preserved exactly — croupier seeds on `(student_id, subpart_id)`, so changing it would break per-student randomization determinism.

## Tests

- `test_shape_and_fields` — snapshot contains every grader/renderer-relevant field, including variable constraints and MCQ options.
- `test_empty_problem_set` — empty set ⇒ `questions == []`, no exception.
- `test_serializer_create_captures_snapshot` — POST through `AssignmentSerializer` populates `assigned_content`.
- `test_snapshot_byte_identical_after_live_edit` — edit `Subpart.correct_answer`, `Subpart.options`, `Question.stem_text`, `ProblemSet.title`, and even `problem_set.questions.clear()`; the assignment's snapshot is still `==` the original. **This is the integrity invariant the rest of Phase 1 depends on.**
- `test_remedial_assignment_has_snapshot` — the remedial-creation path also snapshots.

## Next

- AIV-2a — point `grade_submission` at the snapshot, ship the golden re-grade-after-edit regression test.
- AIV-2b — serve the snapshot in the student assignment-detail serializer.
- AIV-3a — `assigned_count` + `has_graded_submissions` read-only serializer flags (UX only; integrity already guaranteed by AIV-2a).
