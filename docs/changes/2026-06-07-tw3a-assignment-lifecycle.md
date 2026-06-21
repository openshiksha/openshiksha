# TW-3a — Assignment close/reopen lifecycle (backend)

**Classification:** New (Improve over legacy).
**Initiative:** Teacher Workspace.
**Branch:** `feat/2026-06-07-tw3a-assignment-lifecycle`.

## Summary

Adds an additive `Assignment.closed_at: DateTimeField(null=True)` plus
teacher-only `close` / `reopen` actions on `AssignmentViewSet`, a derived
read-only `status` (`active` / `overdue` / `closed`) on the serializer, and
a `SubmissionSerializer.validate` guard that blocks create / update writes
when the target assignment is closed. Reads remain unaffected — students
still see closed assignments labelled as such.

## Why

Legacy had no explicit close — an assignment was "done" only by passing its
due date, so a teacher who wanted to stop accepting late work without
re-dating had to use Django admin. This is the lifecycle primitive TW-3b
(frontend controls) and future reminders/archiving build on.

## Changes

- `backend/openshiksha/apps/core/models.py` — `closed_at` field + `is_closed`
  property + `status` property.
- `backend/openshiksha/apps/core/migrations/0021_assignment_closed_at.py` —
  additive migration.
- `backend/openshiksha/apps/api/views/core.py` — `close` and `reopen` actions
  on `AssignmentViewSet`, idempotent, owner-scoped via the existing
  `assigned_by=user` queryset filter.
- `backend/openshiksha/apps/api/serializers/core.py` —
  `AssignmentSerializer` exposes read-only `closed_at` + derived `status`;
  `SubmissionSerializer.validate` rejects writes against closed assignments.
- `backend/openshiksha/apps/core/admin.py` — surface `closed_at` in list view + filter.
- `frontend_modern/src/types/index.ts` — `Assignment.closed_at` + `status`
  optional fields, ready for TW-3b.
- `backend/openshiksha/apps/api/tests/test_assignment_lifecycle.py` — 9 tests:
  close/reopen happy path, idempotency, non-owner 404, student 403, status
  reflects overdue, submission create + patch blocked when closed, closed
  assignment still readable.

## Verify

- `manage.py check` clean, `makemigrations --check` clean.
- `pytest …test_assignment_lifecycle.py` 9/9; existing
  `test_assignment_api.py` 15/15 still green.
- `npm run type-check` clean.

## Next

TW-3b consumes `status` + the new actions on `TeacherAssignmentDetailPage`.
