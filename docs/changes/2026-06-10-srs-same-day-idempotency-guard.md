# SRS mark-reviewed — same-day idempotency guard (ASA-9)

**Date:** 2026-06-10
**Classification:** Improve (hardening)
**Initiative:** AI Surface Activation — ASA-9 (daily plan 2026-06-10 PR 3)

## Summary

`POST /api/v1/ai/spaced-repetition/{id}/mark-reviewed/` now guarantees the
SM-2 schedule mutates at most once per entry per local day. ASA-3 (#287)
guards client-side (a repeat pass in a sitting is practice-only), but the
endpoint itself would still compound the interval/easiness-factor if called
twice — by a stale tab, a retried request, or a hand-crafted call. The ledger
kept ASA-9 open as the server-side defence-in-depth; this closes it.

## Legacy reference

None — SRS is a modern addition (no legacy equivalent; legacy grading was a
nightly batch in `grader/`).

## Contract

- If `entry.last_reviewed_at` falls on today's local date
  (`timezone.localdate(entry.last_reviewed_at) == timezone.localdate()`):
  - The SM-2 mutation (interval, easiness factor, repetitions,
    next_review_date, last_reviewed_at) is **skipped entirely**.
  - Submitted `answers` are **still graded** and the score returned — the
    practice round stays useful. Grade, don't schedule.
  - Proficiency `Tick`s and the streak update are also skipped (no
    double-counting; the streak is same-day idempotent anyway).
  - Response is `200 OK` with the unchanged serialized entry plus
    `"already_reviewed_today": true`.
- Normal calls keep their exact prior shape, plus
  `"already_reviewed_today": false` (additive only).
- Body validation (400 on bad shapes) is unchanged on both paths.

## What changed

- `backend/openshiksha/apps/ai/views.py` —
  `SpacedRepetitionViewSet.mark_reviewed`: guard computed up front from
  `last_reviewed_at`, early return after grading; docstring documents the
  contract. No model change (`last_reviewed_at` already existed), no
  migration.
- `backend/openshiksha/apps/ai/tests/test_srs_drill_api.py` — new
  `TestMarkReviewedSameDayGuard` (5 tests): schedule unchanged on same-day
  repeat + flag returned; later-day review still updates; guarded call still
  grades answers; no duplicate proficiency ticks; bad bodies still 400.

## Frontend

No change required — `SRSDrillPage` ignores unknown response fields, and
ASA-3 already prevents the double call in-app.

## Tests

`pytest openshiksha/` — 923 passed, coverage 93.76%.

## Next steps

ASA-9 closes the SRS hardening thread. Remaining ASA work: ASA-8 (drill
explanations) and ASA-6 (assignment draft builder) in this batch; ASA-7
(open-response grading UI) as a future batch-anchor.
