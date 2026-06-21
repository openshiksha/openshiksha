# MSO-6 — Replay-safe / idempotent submission writes

**Date:** 2026-06-15
**Initiative:** Mobile Shell & PWA-Offline — Batch 2 (offline write-tolerance)
**Classification:** Improve (hardens a latent re-grade hazard in the grading signal)

## Summary

Hardens the submission write path so a replayed PATCH can never double-grade or
re-grade an already-submitted submission, and a duplicate submit returns the
existing record/score (HTTP 200) instead of erroring. This must land **before**
the client-side offline mutation queue (MSO-7) exists, because an at-least-once
replay queue would otherwise expose a real double-grade hazard.

## The hazard

Grading is triggered by a `post_save` signal
([core/signals.py](../../backend/openshiksha/apps/core/signals.py)):
`grade_submission.delay()` fires whenever `submitted_at` is non-null **and**
(`update_fields is None` **or** `'submitted_at' in update_fields`). DRF's
`ModelSerializer.update()` calls `instance.save()` **without** `update_fields`,
so `update_fields is None` on every PATCH — meaning **any** PATCH to an
already-submitted submission re-fired grading. The frontend hid this by blocking
edits post-submit, but an offline replay queue removes that guarantee.

## What changed

Two independent layers (defense in depth):

1. **Serializer** ([api/serializers/core.py](../../backend/openshiksha/apps/api/serializers/core.py) `SubmissionSerializer`):
   - `validate()` — when the instance is already submitted (`submitted_at is not
     None`), short-circuit before the create/closed-assignment validations so a
     replay returns 200 rather than a 400.
   - `update()` — when the instance is already submitted, return the instance
     **without saving**. A replayed auto-save or duplicate submit becomes a
     harmless idempotent no-op: no signal re-fire, no snapshot mutation. This also
     closes the async double-grade race (a replay arriving while the first grade is
     still pending — `score` still `None` — never re-saves).

2. **Signal** ([core/signals.py](../../backend/openshiksha/apps/core/signals.py)
   `trigger_grading_on_submit`):
   - Added a `score is None` gate: only grade an ungraded submission. A save that
     still carries `submitted_at` on an already-graded submission no longer
     re-grades. The explicit resync re-grade path
     ([api/views/core.py](../../backend/openshiksha/apps/api/views/core.py)) queues
     `grade_submission.delay()` **directly**, bypassing this signal, so it is
     unaffected — verified by the existing resync suite.

## Legacy reference

None — legacy (Django 1.11) was online-only and server-rendered; there is no
offline write path to port. This is a correctness hardening of the modern grading
signal.

## Tests

New `backend/openshiksha/apps/api/tests/test_submission_replay.py`:

- First submit grades exactly once (`grade_submission.delay` called once).
- Replayed submit after grading → 200, **no** second grade, same score.
- Replayed submit before grading completes (score still `None`) → 200 no-op.
- Stale answers auto-save after submit → 200, answers unchanged, no grade.
- Normal pre-submit auto-save unchanged (answers update, no grade).
- Signal-level: re-save of a graded submission does not re-grade; first submit does.

Regression: `test_assignment_api.py` (submission workflow) and
`test_assignment_resync.py` (resync re-grade path) remain green.

## Migration notes

None — no model changes.

## Next steps

MSO-7 — offline mutation queue foundation (frontend) replays onto this now-safe
endpoint.
