# ASA-3 — SRS drill repeat-review guard

**Date**: 2026-06-09
**Classification**: Improve
**Initiative**: AI Surface Activation (ASA-3)

## Summary

The SRS drill result screen's "Review again" button reset `answers`/`result`
and let the student resubmit — calling `mark-reviewed` again and double-moving
the SM-2 interval in one sitting (flagged in the 2026-06-09 polish-backlog
audit). The page now has an explicit phase machine: only the first completed
pass per visit updates the schedule; every later pass is a practice round that
never fires the mutation.

## Legacy reference

None — spaced repetition is modern-only. Audit reference:
`docs/ai-features/polish-backlog.md` (2026-06-09 entry).

## What changed

- `frontend_modern/src/features/student/SRSDrillPage.tsx`
  - New `DrillPhase` state: `review → reviewResult → practice → practiceResult`
    (practice loops). First-pass behaviour is unchanged.
  - Graded result screen: button renamed "Practice again" with sub-line
    "Extra practice won't change your review schedule."
  - Practice phase: brand-tinted banner on the form, submit button reads
    "Finish Practice", and submission **skips `markReviewed` entirely** —
    completion shows a "Practice round complete!" screen confirming the next
    review date is unchanged.
- `frontend_modern/src/features/student/SRSDrillPage.test.tsx` (new) —
  QuestionCard stubbed (its rendering is covered by its own tests).

## Deviation from plan

The plan suggested grading the practice round locally "since the page already
computes correctness for display" — it doesn't (grading is server-side via
`mark-reviewed`, and the student payload carries no correct answers). The
practice-round completion screen is therefore unscored; the guard itself (no
second SM-2 update) is unaffected.

## Tests

`npx vitest run SRSDrillPage` — 3 tests passing:
1. First submit POSTs `mark-reviewed` once and shows the graded result.
2. Second pass shows practice-round copy and never re-fires the mutation.
3. Chained practice rounds still total exactly one POST.

`npx tsc --noEmit` + `npm run lint` clean.

## Migration notes

None — frontend only. Backend idempotency guard (reject/no-op a second
same-day review of the same entry) remains ASA-9 in the initiative backlog as
defence-in-depth; a fresh page visit on the same day is still unguarded until
then (documented, accepted).

## Next steps

ASA-4 and ASA-5 in this batch.
