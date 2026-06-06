# 2026-06-06 — IW-6 · Library expansion (`function-plotter`, `fraction-bar`)

## Summary

Two more first-party widgets land via the IW-8 scaffolder, taking the
teacher gallery from "thermo + number-line" to a real library across
the curriculum:

- **`function-plotter`** — explanatory math widget that plots
  `y = f(x)` over a configurable domain. Ships a tiny in-sandbox
  recursive-descent parser so widget source stays free of `eval()` /
  `Function()`.
- **`fraction-bar`** — explanatory primary-school widget showing
  `numerator / denominator` as a shaded bar with two render modes
  (`shaded` for "name the fraction" questions, `labelled` for
  worked-solutions / hints).

Both kinds were already in the backend's `KNOWN_WIDGET_KINDS` set
(seeded in IW-3a), so the writable serializer accepted them all along —
this PR ships the actual frontend implementations + the gallery
schemas.

## Classification

**New.** No legacy analogue.

## What changed

- **`src/widgets/function-plotter/`** (new) — `defineWidget` with a
  hand-rolled tokeniser + recursive-descent parser inside the
  sandboxed render. Grammar covers: numbers; identifiers (`x`, `pi`,
  `e`); `+ - * / **` with standard precedence (right-assoc `**`);
  unary `+` / `-`; function calls with arities 1 + 2; parentheses.
  Whitelisted functions: `sin cos tan asin acos atan log ln log10
  exp sqrt abs floor ceil round` (unary) + `pow min max` (binary).
  200-sample polyline; vertical asymptotes break the path naturally
  (`M`-vs-`L` on first valid sample after a discontinuity).
- **`src/widgets/fraction-bar/`** (new) — `defineWidget` rendering
  the bar in SVG. Defensive clamps on `denominator` ∈ [1, 40] and
  `numerator` ∈ [0, denominator] so a "5/4" or "1/0" mistake renders
  something coherent instead of crashing. Two render modes via a
  `mode: "shaded" | "labelled"` enum.
- **`src/widgets/registry.ts`** — both kinds registered at the IW-8
  anchors (one-line additions).
- **`src/features/design/DesignSystemPage.tsx`** — two new sections
  showcasing the widgets:
  - `function-plotter` with `y = sin(x) + ½x` over `[-6, 6] × [-4, 4]`
  - `fraction-bar` side-by-side (3/8 shaded vs 5/12 labelled)
- **Tests** — 6 cases each for the two widgets covering identity,
  registry round-trip, `paramsSchema` presence, render-source
  invariants (no `eval` / `Function`; parser symbols present;
  function whitelist intact; defensive clamps in `fraction-bar`;
  friendly error band in `function-plotter`).

## Test plan

- `npm test` — **73 passed** in `src/widgets/` (was 61; +12 across
  the two new widgets)
- type-check / lint / build all clean
- Backend untouched — `KNOWN_WIDGET_KINDS` already had both kinds
  since IW-3a, so the writable serializer accepts them without
  further migration

## Gallery surface

With IW-5 (#221) already merged, both new widgets surface in the
teacher gallery in `CreateQuestionPage` automatically: each kind's
`params.schema.json` drives the auto-generated config form, and the
live preview re-renders on every keystroke. No teacher gallery code
needed an edit.

## Next

- *(Follow-up)* `/widgets/dev` playground — the IW-8 backlog item the
  scaffolder PR deferred
- *(Follow-up)* `migrate_legacy_interactive_html` management command
- **IW-9 (full)** + **IW-10** — Widget Studio runtime + UI (Tier-2
  visual builder)
- **IW-11** — Studio polish + power features
