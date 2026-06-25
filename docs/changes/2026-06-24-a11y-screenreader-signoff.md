# 2026-06-24 — A11Y-17: screen-reader sign-off scaffold + announce-region audit

## Summary

Two-part increment for **Batch 4** (DoD item 5) of the
[Accessibility — WCAG 2.1 AA](../initiatives/2026-accessibility-wcag-aa.md)
initiative:

1. **Screen-reader sign-off scaffold** — a structured NVDA (Windows) + VoiceOver
   (mac/iOS) manual test script, `docs/initiatives/a11y/screen-reader-signoff.md`,
   with a per-journey table (sign-in, register, browse, **practice + submit**,
   parent dashboard), expected announcements, and pass/fail columns. This is the
   manual evidence template a human runs to close DoD item 5.
2. **Announce-region audit + fix** — audited the app's dynamic regions for correct
   live-region semantics and fixed the one real gap.

## Classification

**Docs** (sign-off scaffold) + **Improve** (live-region fix).

## Legacy reference

None — legacy Django 1.11 had no live-region / status-message semantics.

## What changed

### Fix: announce the post-submit score (WCAG 4.1.3 Status Messages)

`student/AssignmentDetailPage.tsx` — the post-submit outcome card (score /
"grading…" / "submitted offline") appears **dynamically** after the student
submits, but had no live-region semantics, so a screen-reader user heard nothing.
Added `role="status"` + `aria-live="polite"` to that card so the result is
announced politely (without stealing focus) once the SR finishes the current
utterance.

The audit confirmed the other named dynamic regions were already correct:
- "Saved on this device · will sync" — `SyncStatus.tsx` (`role=status`, MSO-8) ✅
- offline/reconnect + app-update banners, announcements banner, loading
  spinners/skeletons — all already live regions ✅
- the app has **no global toast** (status is inline), so there was nothing to fix
  there.

The one remaining gap (dialog focus-trap/restore on the QuestionBank side-sheet)
is documented in the sign-off doc as the Batch-4 follow-up.

## Tests

- `student/AssignmentDetailPage.offline.test.tsx` — extended the score-reconcile
  case to assert the revealed score sits in a `getByRole('status')` region with
  `aria-live="polite"` and the score text. **3/3 pass.**
- `npx tsc --noEmit` + `eslint` — clean.

## Migration notes

None — frontend + docs only.

## Next steps

- Run the NVDA/VoiceOver script and record sign-off → closes DoD item 5.
- Implement + gate the dialog focus-trap / focus-restore behaviour.
