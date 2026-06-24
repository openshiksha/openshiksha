# 2026-06-23 — A11Y-8: gate the student core-loop routes + Batch 2 close-out

## Summary
Flips the four authenticated **student core-loop** routes in the per-route axe
harness from reporting-mode to **`gate: true`**, turning CI's `frontend-e2e` job
into a regression gate for the student dashboard, assignment detail, proficiency,
and SRS drill. This closes **Accessibility Batch 2** — the measured-and-enforced
WCAG 2.1 AA contract now covers the part of the product students actually live in,
not just the public front door.

## Classification
**New (gate) + Docs** — no app/source changes; one test-table edit plus
documentation. The remediation that made gating safe landed earlier in the batch
(A11Y-4 #417, A11Y-FV #418, A11Y-6 #419, A11Y-7 #420).

## What changed
- `frontend_modern/e2e/a11y.spec.ts`: the four `auth: true` student routes
  (`/student`, `/student/assignments/1`, `/student/proficiency`,
  `/student/srs-drill/1`) flip `gate: false` → `gate: true`. Each now asserts
  `blocking === []` (zero serious/critical WCAG AA violations).
- `docs/a11y/2026-06-23-student-core-loop-manual-checklist.md` (new): keyboard-only
  + screen-reader walkthrough of the dashboard → assignment → submit → proficiency
  → drill loop — the WCAG behaviours axe can't measure.
- `docs/initiatives/2026-accessibility-wcag-aa.md`: ledger rows for A11Y-4
  (resolved, supersedes the deferred row), A11Y-FV, A11Y-6, A11Y-7, A11Y-8;
  DoD item 4 marked done.
- `docs/initiatives/STATUS.md`: Batch 2 recorded as shipped; next phase set to
  Batch 3 (teacher/parent surfaces).

## Why this is safe to gate now
The A11Y-6 authenticated baseline (#419) found all four student routes
**structurally clean** — zero label/landmark/heading violations. The only blocking
finding was `color-contrast` on the `StreakBadge` secondary labels, fixed in A11Y-7
(#420) by dropping the `opacity-70`/`opacity-60` that dragged tinted text below
4.5 : 1. The brand-button contrast that blocked gating the public hero was already
resolved by A11Y-4's `brand-700 → #C05300` token sweep (#417). Re-running
`npx playwright test a11y` locally: **11/11 pass**, with `total: 0, blocking: []`
on every student route. Residual `color-contrast` shows up only in axe's
`incomplete` bucket (a background axe can't compute), which is recorded but does
not gate — the same contract the public routes already use.

## Tests
- `npx playwright test a11y` — 11 passed (44 s). The four student routes now run
  under the gate assertion and pass with `blocking === []`.

## Migration notes
None. Test-only + docs.

## Next steps
- **Batch 3** — teacher / parent surfaces: reuse the `e2e/support/auth.ts`
  authenticated harness (add teacher/parent users + their core reads), baseline →
  remediate → gate. (DoD item 6.)
- **Batch 4** — full keyboard-only walkthrough + screen-reader (NVDA/VoiceOver)
  sign-off. (DoD item 5.)
