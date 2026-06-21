# MPN-5 — Wire due-date reminders to Web Push

**Date:** 2026-06-17
**Initiative:** Mobile Shell & PWA-Offline → web-push later-phase
**Classification:** Improve
**Depends on:** MPN-2 (`send_web_push` helper)

## Summary

Extends the existing `send_due_date_reminders` Celery task to **also** fan out a
Web Push notification to subscribed students, reusing the same cadence,
eligibility, and idempotency logic as the email channel — so the two channels can
never drift. Push is additive: email remains the source of truth.

## What changed

- **`core/emails.py`** — `build_due_reminder_push(student, title, due_str)`
  returns a localized `{title, body}` push payload from a terse en/hi `_PUSH`
  catalog, sharing the student's `preferred_language` with the email path.
- **`core/tasks.py` — `send_due_date_reminders`**:
  - A single `email_reminders_opt_out` now governs **both** channels (v1
    decision — one toggle for email + push; a separate `push_reminders_opt_out`
    can be added later if needed).
  - Eligibility broadened: a student is reminded if they have **email OR a push
    subscription** (previously email-only). A student with neither is skipped so
    the idempotency row isn't burned.
  - For eligible students: email is sent if they have an address; push is sent if
    they have a subscription. The payload adds `url` (`/student/assignments/<id>`
    deep link) and `tag` (`assignment-<id>`, collapses duplicate reminders).
  - The push fan-out goes through `send_web_push`, which never raises into the
    task — a dead endpoint can't abort a reminder run.

## Tests

`core/tests/test_due_date_reminders.py` — added `TestDueDateReminderPush`:
- push sent (with correct payload `title/body/url/tag`) for a subscribed student;
- push **not** sent for an opted-out student;
- a **no-email but subscribed** student is still push-reminded (no email sent).
Existing email tests unchanged and green (12 total in the file).

## Migration notes

None — no model changes.

## Manual verification

See `docs/perf/2026-06-17-pwa-push-manual-test.md`.

## Next steps

MPN-4 (frontend opt-in hook + ProfilePage toggle) is the remaining batch item —
it lets a student actually create the subscription this task delivers to.
