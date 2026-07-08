# The widget review bar — what a new widget must clear to ship

> Companion to [`anatomy.md`](./anatomy.md) (the SDK reference) and
> [`build-your-first-widget.md`](./build-your-first-widget.md) (the 10-minute
> loop). This page is the **reviewer's checklist** — and therefore the
> contributor's target. If your PR clears every bar below, review is fast.

**Widgets are code, and code ships only through pull-request review.** This is
different from question content: [content packs](../../contrib/packs/README.md)
are schema-validated *data* and flow through the in-app approval pipeline. A
content pack can *use* any registered widget kind via `widget_kind` +
`widget_config`, but it can never introduce one. If you want a new widget,
start with a [widget proposal issue](https://github.com/openshiksha/openshiksha/issues/new?template=widget_proposal.md)
so we can agree on scope before you build.

## 1. Sandbox rules (non-negotiable)

The widget runtime is a sandboxed `allow-scripts` iframe — deliberately
**without** `allow-same-origin` — and your `render` function is serialised via
`Function.prototype.toString()` and inlined into it. Concretely:

- **No network.** The sandbox is network-less by design. No `fetch`, no
  `XMLHttpRequest`, no WebSocket, no external `<script>`/`<img>` URLs.
- **No imports, no closures.** `render` must be self-contained — it cannot
  reference anything outside its own body (helpers must be inlined; see the
  `step-solver` precedent for inlining an entire engine).
- **No `eval` / `new Function` / injected `<script>`.** Config is *data*,
  interpreted — never executed.
- **Deterministic.** Same config + variables ⇒ same widget. Per-student
  randomization comes from croupier `{{var}}` substitution upstream, not from
  unseeded randomness inside the widget.
- **AI never lives in the sandbox.** Any AI surface is host-side (see the
  step-solver's wrong-step coach), and AI is never in the grading path.

## 2. Schema (both copies)

- `params.schema.json` in your widget folder: Draft 2020-12, with
  `additionalProperties: false`, sensible bounds/defaults, and a description
  per field — the teacher config form is generated from it.
- The **vendored backend copy** in
  `backend/openshiksha/apps/core/data/widget_schemas/<kind>.schema.json`, plus
  your kind added to `KNOWN_WIDGET_KINDS` in
  `backend/openshiksha/apps/core/widgets.py`. Server-side validation is the
  pipeline's safety floor (DTB-1) — a widget without it doesn't ship.
- The parity test (`test_widget_fields.py`) fails if the two copies drift, and
  the per-kind config test battery needs a valid + an invalid config for your
  kind.

## 3. Answer reporting (if your widget grades)

An answer-producing widget reports through `ctx.reportValue(v)` — the value
crosses the postMessage boundary and lands in the **existing deterministic
per-subpart grader**. Rules:

- Don't call `reportValue` at mount; a question must be leavable blank.
- Report a value the grader can actually mark (numeric answers should respect
  your own snapping/precision — the "¾ on a step-0.25 axis" bug class).
- Never grade inside the widget; the widget reports, the grader decides.
- Explanatory widgets simply never call `reportValue`.

## 4. Accessibility

- **Keyboard-operable end to end** — every interaction reachable without a
  pointer (the `number-line` slider's Home/arrow-key path is the precedent).
- Real semantics: `role`, `aria-valuenow`/`aria-valuemin`/`aria-valuemax` on
  slider-likes, labelled controls, visible focus.
- Respect `prefers-reduced-motion` for any animation.

## 5. Tests

- A Vitest file in your widget folder: module surface (registry entry, schema
  loads) + executed-render behaviour (happy-dom can run your `render` with a
  fake `ctx` — see `step-solver`'s suite for the pattern).
- Backend: the valid/invalid config pair for the per-kind battery.
- If you inlined a copy of shared logic into `render`, add an **anti-drift
  test** comparing the widget's behaviour to the canonical implementation.

## 6. The PR itself

- One widget per PR: the folder, the registry line, the vendored schema +
  `KNOWN_WIDGET_KINDS`, tests, and a README in your widget folder.
- `npm run lint && npx tsc --noEmit && npx vitest run` green;
  `python -m pytest` green.
- A screenshot or short GIF from `/widgets/dev?kind=<your-kind>` in the PR
  description so reviewers see it before they run it.
