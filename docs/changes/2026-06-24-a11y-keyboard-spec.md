# 2026-06-24 — A11Y-16: automated keyboard-traversal spec (Batch 4 kickoff)

## Summary

Added `frontend_modern/e2e/keyboard.spec.ts` — the first **behavioural**
accessibility gate, complementing the static axe gate (`a11y.spec.ts`). Where axe
checks labels/contrast/landmarks, this spec drives the keyboard and asserts
operability that axe cannot see. It begins **Batch 4** of the
[Accessibility — WCAG 2.1 AA](../initiatives/2026-accessibility-wcag-aa.md)
initiative (DoD item 5 — keyboard-only + screen-reader sign-off).

## Classification

**New** — net-new automated test coverage; no production code change.

## Legacy reference

None — legacy Django 1.11 had no keyboard-operability story or automated checking.

## What changed

`e2e/keyboard.spec.ts`, reusing the authenticated harness (`support/auth.ts`), with
two assertions:

1. **WCAG 2.4.1 Bypass Blocks** — on `/student`, the first `Tab` focuses the
   "Skip to main content" link; pressing `Enter` moves focus into the
   `#main-content` landmark.
2. **WCAG 2.1.2 No Keyboard Trap** — on `/student/assignments/1`, tabbing 25 times
   lands on several distinct, real focus stops and never gets stuck (focus is
   never lost to `<body>` for the whole run). Proves no control traps focus.

The spec is picked up automatically by the `frontend-e2e` CI job — `npm run
test:e2e` runs `playwright test --grep-invert @visual`, i.e. every non-visual
spec — so no workflow change was needed.

## Tests

- `npx playwright test e2e/keyboard.spec.ts` — **2/2 pass**.
- `npx tsc --noEmit` + `npx eslint e2e/keyboard.spec.ts` — clean.

## Deferred (Batch 4 follow-up)

The QuestionBank "Add to set" side-sheet (`AddToProblemSetSheet`) already moves
focus inside on open and closes on Escape, but does **not** yet implement a true
focus *trap* (Tab cycling bounded within the dialog) or focus *restore* (returning
focus to the trigger on close). Gating those requires the remediation first; both
are tracked in the A11Y-17 screen-reader sign-off doc as the remaining WCAG 2.4.3
/ 2.1.2 work for the dialog pattern. (Separately noted: deep-linking
`/teacher/questions` currently lands on `/teacher` under the preview server — worth
its own investigation, and the reason the dialog assertion isn't gated here yet.)

## Migration notes

None — test-only, no backend or schema changes.

## Next steps

- A11Y-17 — screen-reader sign-off scaffold + announce-region (`aria-live`/`role=status`) audit.
- Implement + gate the dialog focus-trap / focus-restore behaviour.
