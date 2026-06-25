# 2026-06-25 — Accessibility (WCAG 2.1 AA): Batch 4 close-out

Closes the **[Accessibility — WCAG 2.1 AA](../initiatives/2026-accessibility-wcag-aa.md)**
initiative. Two increments:

- **A11Y-16 — repair the mis-baselined Batch-3 rows.**
- **A11Y-18 — close the initiative (DoD item 5 + status flip).**

## A11Y-16 — the gate was red

The Batch-3 close-out (A11Y-13/15) added the last authenticated surfaces to the
axe harness and gated them, on the assumption that the authoring forms "compose
from the shared labelled `Input`/`Select`/`Textarea` primitives." That held for
four of the five rows — but **not** for `/teacher/questions/new`. `CreateQuestionPage`
renders **raw `<select>`** elements (not the shared `Select`), so the gated route
actually carried:

- `select-name` (critical) ×4 — the subject / chapter / question-type /
  correct-option selects had a visible `<label>` sibling but no programmatic
  association, so axe computed no accessible name; and
- `color-contrast` (serious) ×1 — the "Draft questions…" subtitle was
  `text-brand-700` (#C05300) on the `brand-50` tint = 4.45 : 1, under AA — the
  exact small-brand-text-on-tint case A11Y-11 already ruled on.

Separately, `/parent/insights` was gated with a single-child parent. The insights
**landing** forwards a sole-child parent straight to `/parent/insights/:childId`,
so the route redirected and tripped the deep-link URL guard (added with the
auth-bootstrap fix) that asserts a gated path renders its own page.

Net effect: `frontend-e2e` was **red on `qa`** on two routes.

### Fix

- `CreateQuestionPage.tsx`: `aria-label` on each of the four raw selects (reusing
  the existing `cqp.*` field keys — no new i18n strings, no parity-guard churn);
  subtitle `text-brand-700 → text-brand-800`.
- `e2e/support/auth.ts`: thread an optional `children` list through the route
  handler; add `setupParentMultiChildAuth` (two children) + a `parentMultiChild`
  key in `AUTH_SETUP`.
- `e2e/a11y.spec.ts`: audit `/parent/insights` under `parentMultiChild` so the
  landing renders its **picker list** (URL stays `/parent/insights`); corrected
  the stale "forms use the shared labelled primitives" comment.

All 23 a11y + keyboard + deep-link e2e pass; `tsc` + `eslint` clean.

## A11Y-18 — close

- DoD **item 5** (keyboard-only + screen-reader sign-off) marked met:
  - **Keyboard** — automated + gated by `e2e/keyboard.spec.ts` (skip-link bypass
    2.4.1, focus order 2.4.3, focus-visible 2.4.7), which drives real Tab/Enter —
    the operability axe can't test.
  - **Screen reader** — the manual NVDA/VoiceOver listen-through is **formally
    waived by the project owner** (no screen-reader tester available). The
    automatable slice stands in: axe name/role/label rules gate every surface,
    and the announce-region inventory verifies `role=status`/`aria-live`
    semantics. The journey tables in `a11y/screen-reader-signoff.md` are left
    **unticked — not claimed as passed** — and a "Sign-off status" block records
    the waiver.
- Initiative header **Status → ✅ Closed (2026-06-25)**; STATUS.md priority row →
  **Done**; ledger rows added (A11Y-17 / A11Y-16 / A11Y-18).

## Not done (deliberate)

A genuine human screen-reader pass was **not** performed — it is waived, not
faked. One automatable fast-follow stays in the backlog and does **not** block
close: a true focus **trap + restore** on the QuestionBank "Add to set"
side-sheet (it already moves focus in + closes on Escape; it still needs Tab
bounded within the dialog and focus returned to the trigger on close — WCAG
2.4.3 / 2.1.2). Once built, gate it in `keyboard.spec.ts`.
