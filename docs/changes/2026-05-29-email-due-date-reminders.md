# Email due-date reminders (P5)

**Date**: 2026-05-29
**Classification**: New (legacy had no automated due-date reminder)
**Branch**: `feat/2026-05-28-email-due-date-reminders` (based on `modernization`)

## Summary

A Celery-beat periodic task emails students before their assignments are due,
with a per-student opt-out. Reminders are idempotent — each student is emailed at
most once per assignment.

## What changed

**Backend**
- `core.User.email_reminders_opt_out` (BooleanField, default False) — per-student
  opt-out. Exposed read+write through `/api/v1/users/me/` and `/users/me/profile/`.
- New model `core.AssignmentReminder` (`assignment`, `student`, `sent_at`,
  `unique_together(assignment, student)`) — an idempotency log; one row per reminded
  (assignment, student) pair.
- `core.emails.notify_due_date_reminder(student, title, due_str)` — the reminder email
  (fail-silent, mirrors the existing notification helpers).
- `core.tasks.send_due_date_reminders(window_hours=24)` — periodic task: finds active
  assignments due within the window and reminds every enrolled student who has an
  email, hasn't opted out, hasn't submitted, and hasn't already been reminded. The
  `AssignmentReminder` row is created *before* sending so a crash mid-run never
  double-emails. Targeted (per-student remedial) assignments remind only their target.
- `CELERY_BEAT_SCHEDULE` in `settings/base.py` — runs daily at 06:00 Asia/Kolkata.
- Migration `core/0012_user_email_reminders_opt_out_assignmentreminder.py`.

**Frontend**
- `User.email_reminders_opt_out` added to the type and `authApi.updateProfile` payload.
- ProfilePage shows an "Assignment due-date reminders" toggle for students (checked =
  receiving; unchecking opts out), saved via the existing profile mutation.

## Tests

`core/tests/test_due_date_reminders.py` — 9 tests: reminder sent for upcoming
assignment; no duplicate on re-run; opted-out / submitted / no-email students skipped;
out-of-window and past-due assignments ignored; targeted assignment reminds only the
target; custom `window_hours`. Full backend suite green. Frontend `tsc` + lint clean.

## Operational notes

- Requires a Celery **beat** scheduler process in addition to the worker
  (`celery -A openshiksha beat`). In development, `CELERY_TASK_ALWAYS_EAGER` means the
  task runs synchronously if invoked directly; beat scheduling applies in
  worker-backed environments.
- Window and cadence are adjustable via `CELERY_BEAT_SCHEDULE` / the task's
  `window_hours` kwarg.
