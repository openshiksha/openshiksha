# 2026-06-24 — A11Y-13/15: authoring forms + parent insights gated (Batch 3 close-out)

## Summary

Extended the gated WCAG 2.1 AA axe contract onto the **last unmeasured
authenticated surfaces** — the dense teacher authoring forms and the parent
insights pages — fully satisfying **DoD item 6** of the
[Accessibility — WCAG 2.1 AA](../initiatives/2026-accessibility-wcag-aa.md)
initiative. Five routes were added to the per-route axe harness and, because the
baseline came back clean, gated directly:

- `/teacher/questions/new` (`CreateQuestionPage`)
- `/teacher/assignments/new` (`CreateAssignmentPage`)
- `/teacher/problem-sets/new` (`CreateProblemSetPage`)
- `/parent/insights` (`ParentInsightsLandingPage`)
- `/parent/insights/:childId` (`ParentInsightsPage`)

All five compute `blocking === []` (zero serious/critical axe violations). The
only residual is `color-contrast` in axe's **`incomplete`** bucket (a background
axe can't compute) — recorded but non-gating, the same contract as every other
gated route.

## Classification

**New** (gate the last authenticated surfaces) + **Improve** (latent crash fix) +
**Docs** (Batch 3 close-out).

## Legacy reference

None to port — legacy Django 1.11 templates (`sphinx/`) had no labels-for, no
fieldset grouping, no automated a11y checking. This is net-new platform capability
(an enforced AA gate over the modern authoring/insights surfaces).

## What changed

### Harness (`frontend_modern/e2e/`)

- **`a11y.spec.ts`** — added the five routes above to the `ROUTES` table with
  `gate: true`.
- **`support/auth.ts`** — added the object/list reads these pages need so they
  render past their loading states to a visible `h1`:
  - `/subject-rooms/` → one `TEACHER_SUBJECT_ROOM` (the authoring forms swap their
    class `<Select>` for a "no rooms" message when the list is empty, hiding the
    very controls axe must scan; one row renders the labelled selects).
  - `/chapters/` → one `CHAPTER`.
  - `/ai/parent-summaries/latest/` → `404`, so `ParentInsightsPage` renders its
    "No summary yet" empty state (which carries the `h1`) via the hook's existing
    404→null contract — a paginated-empty body would be the wrong shape.

### Latent crash fix (`support/auth.ts`)

Seeding a subject room makes the **teacher dashboard** render
`ClassroomCodeWidget` (previously never exercised by the gated `/teacher` route,
because the empty-rooms dashboard skips it). That widget reads the **bare-array**
endpoint `/users/me/classroom-code/`, but the harness catch-all returns a
*paginated object*, so `codes?.find(...)` threw `TypeError: codes?.find is not a
function` and tripped the ErrorBoundary. Added an explicit `[]` stub for that
endpoint. Net effect: the teacher-dashboard gate now actually covers
`ClassroomCodeWidget`, closing a blind spot.

## Why A11Y-14 (remediation) was a no-op

The day's plan staged this as baseline (A11Y-13) → remediate (A11Y-14) → gate
(A11Y-15), anticipating unlabelled inputs / heading-order / contrast findings on
the dense forms. The baseline disproved that premise: every form control is built
from the shared `Input` / `Select` / `Textarea` primitives
(`src/shared/ui/Input.tsx`), which already wire `<label htmlFor>` +
`aria-describedby`, and each page leads with a single `h1` (`SectionHeading
as="h1"` or a literal `<h1>`). With `blocking === []` on all five routes there was
nothing to remediate, so the empty A11Y-14 step was collapsed and the rows gate
directly — mirroring the A11Y-3 / A11Y-9 precedent where the public and
teacher-core baselines also came back structurally clean.

## Tests

- `npx playwright test e2e/a11y.spec.ts` — **20/20 routes pass**, including the
  five newly-gated routes asserting `blocking === []` and the teacher-dashboard
  route now rendering `ClassroomCodeWidget`.
- `npx tsc --noEmit` — clean.
- `npm run lint` — clean (`--max-warnings 0`).

## How to verify

```bash
cd frontend_modern
npx playwright test e2e/a11y.spec.ts
# inspect the baselines:
cat axe-report/teacher-create-question.json | jq .summary.blocking      # []
cat axe-report/parent-insights-child.json   | jq .summary.blocking      # []
```

## Migration notes

None — frontend + docs only, no backend or schema changes.

## Next steps

- **Batch 4 (DoD item 5)** — automated keyboard-traversal spec
  (`e2e/keyboard.spec.ts`: skip-link, no-trap, dialog focus-trap + Escape) and a
  screen-reader (NVDA/VoiceOver) sign-off scaffold + announce-region audit.
- Once Batch 4 lands, consider an axe CI job over authenticated routes against the
  full Docker stack (real data instead of stubs).
