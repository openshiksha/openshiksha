# MSO-9 — Offline final-submit

**Date:** 2026-06-15
**Initiative:** Mobile Shell & PWA-Offline — Batch 2 (offline write-tolerance)
**Classification:** New

## Summary

Lets a student **submit an assignment while offline**. The submit optimistically
flips to a submitted view immediately with honest "Submitted — will be graded
when you're back online" copy (no fake score); the submit mutation is queued
(MSO-7) and replays onto the idempotent server (MSO-6) when the network returns,
at which point the real score reconciles into the card. If the replay ultimately
fails (e.g. the assignment closed while offline), the form re-opens so the student
isn't stuck.

## What changed

`src/features/student/AssignmentDetailPage.tsx`:
- `useOnlineStatus()` + a new `submittedOffline` state.
- `handleSubmit` now **optimistically** locks into the submitted view immediately
  (`setIsSubmitted(true)`), sets `submittedOffline` when offline at submit time,
  then fires the queued `patchSubmission.mutate`. Its `onSuccess` (fires
  immediately online, or after the queued replay) reconciles the real score and
  clears `submittedOffline`; its `onError` re-opens the form.
- The post-submit card gains a **pending-grade** variant: when `submittedOffline`,
  it shows `submittedOfflineTitle` + `gradePending` on the neutral `brand-50`
  surface (not a red/amber/green score band), resolving to the real band once the
  score arrives.
- i18n: `assignmentDetail.submittedOfflineTitle` + `assignmentDetail.gradePending`
  in `en.ts` + `hi.ts` (full parity).

## Notes

- Grading is async (Celery) even online, so the PATCH `score` is already
  frequently `null` on submit until the task runs — the component already handled
  that. Offline simply widens the existing "score not yet available" window with
  honest copy.
- Double-submit safety: if the student taps submit, goes online, and a manual
  re-submit races the replay, MSO-6's idempotent guard makes the second a no-op
  returning the same score.

## Legacy reference

None — legacy was online-only; submitting required a live connection. This is new
capability built on the MSO-6 idempotent server + MSO-7 queue + MSO-8 sync UX.

## Tests

`src/features/student/AssignmentDetailPage.offline.test.tsx` (mocks the data +
mutation hooks, drives connectivity): offline submit → optimistic
"will be graded when you're back online" + no `%` score + locked inputs + queued
mutation carrying `submitted_at`; replay `onSuccess` → real `80%` reconciles and
the offline copy clears; replay `onError` → form re-opens (editable). Student
suite (54) + parity guard + tsc + lint + build + bundle budget (146.00 kB ≤
160 kB) green.

## Next steps

MSO-10 — batch close-out: manual offline-write test checklist, ledger rows, and
the STATUS headline flip.
