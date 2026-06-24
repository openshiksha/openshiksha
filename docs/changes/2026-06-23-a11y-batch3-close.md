# 2026-06-23 — A11Y-12: gate the teacher + parent routes + Batch 3 close-out

## Summary
Flips the four authenticated **teacher + parent** core surfaces in the per-route
axe harness to **`gate: true`**, turning CI's `frontend-e2e` job into a regression
gate for the teacher dashboard, question bank, AI grading queue, and parent
dashboard. This closes **Accessibility Batch 3** — the measured-and-enforced WCAG
2.1 AA contract now covers the public front door, the student core loop, *and* the
teacher/parent core surfaces.

## Classification
**New (gate) + Docs** — one test-table edit plus documentation. The remediation
that made gating safe landed earlier in the batch (A11Y-9 baseline #442, A11Y-11
contrast fix #450).

## What changed
- `frontend_modern/e2e/a11y.spec.ts`: `/teacher`, `/teacher/questions`,
  `/teacher/grading`, `/parent` flip `gate: false` → `gate: true` (each asserts
  `blocking === []`).
- `docs/a11y/2026-06-23-teacher-parent-manual-checklist.md` (new): keyboard-only +
  screen-reader walkthrough of the gated teacher/parent surfaces.
- `docs/initiatives/2026-accessibility-wcag-aa.md`: ledger rows A11Y-8/9/11/12 with
  PR links; DoD item 6 marked partial (core surfaces gated; authoring forms +
  parent insights deferred).
- `docs/initiatives/STATUS.md`: Batch 3 recorded; next phase set to Batch 4
  (full keyboard/SR sign-off) + the deferred dense authoring surfaces.

## Why this is safe to gate
The A11Y-9 baseline (#442) found the teacher surfaces structurally clean
(`blocking: []`). `/parent` had one blocking `color-contrast` node (small
`brand-700` text on the `brand-50` tint = 4.45 : 1), fixed in A11Y-11 (#450) by
moving small brand text on a brand tint to `brand-800`. Re-running
`npx playwright test a11y`: **15/15 pass**, all four routes `blocking: []`.
Residual `color-contrast` stays in axe's `incomplete` bucket (non-gating) — the
same contract as the public + student routes.

## Scope (deliberately deferred, noted not gated)
Per the Batch-1 lesson (never gate a dirty route), the dense teacher authoring
forms (`CreateQuestionPage`, `CreateAssignmentPage`, `CreateProblemSetPage`) and
the parent insights pages were not baselined/gated this batch — they carry richer
form interactions that likely need a dedicated label/landmark pass. They stay
reporting-candidate for a future Batch-3 increment.

## Tests
- `npx playwright test a11y` — 15 passed; the four teacher/parent routes now run
  under the gate assertion with `blocking: []`.

## Migration notes
None. Test-only + docs.

## Next steps
- A future increment baselines + gates the authoring forms + parent insights.
- **Batch 4** — full keyboard-only walkthrough + screen-reader (NVDA/VoiceOver)
  sign-off (DoD item 5).
