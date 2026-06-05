# Interactive Widgets Framework — Initiative

> **North Star:** Authoring a new interactive educational widget (a piston
> simulation, a number line, a function plotter, a circuit builder) should be
> as easy as picking it from a gallery and filling in a form. Building a new
> *kind* of widget should be **a single file** with one `defineWidget(...)`
> call and a working dev playground — no plumbing, no `postMessage` boilerplate.
> Rendering one should be **safe by construction**, never a raw-`<script>` XSS
> hole.
>
> **Status:** 🟢 **Active** (promoted 2026-06-04 — M7-11 sandbox seed shipped
> in #132 / `4af87a9a`, V2 "Chalk & Unlock" essentially closed).

**Last updated:** 2026-06-04

---

## A. Why this initiative exists

The legacy platform marketed *"educational games, interactive widgets"* and
shipped exactly one true example: the Class 11 Thermodynamics piston/First-Law
simulation (`openshiksha-cabinet/questions/raw/1/1/11/3/44/22.json`). It was
authored as **bespoke raw HTML + SVG + inline jQuery `<script>`** embedded in
the question content. That approach is a dead end for three reasons:

1. **Insecure.** Raw author `<script>` injected into the app DOM is the exact
   XSS risk DOMPurify exists to block. The modern renderer correctly strips it
   — which *silently kills the widget*.
2. **Not reusable.** Every widget re-hand-wrote its own SVG, slider, and event
   loop. There is no shared slider, no shared plot, no shared anything. A
   second widget meant starting from zero.
3. **Unauthorable.** Only someone who could hand-write SVG + jQuery could make
   one. Teachers and content authors had no path to create interactive content.

**M7-11** (the closing slice of [Cabinet Data Fidelity](cabinet-data-fidelity.md))
rescues the *one* legacy widget by preserving its HTML and rendering it in a
sandboxed iframe — see [`InteractiveWidget.tsx`](../../frontend_modern/src/shared/ui/InteractiveWidget.tsx).
This initiative is the **forward-looking** sequel: turn that one-off rescue
into a **framework** where interactive widgets are first-class, reusable,
safe, **and a joy to author** — so the platform can actually deliver on the
"interactive learning" promise at scale, *and* attract contributors who want
to build educational content.

---

## B. Design principles

1. **Safe by construction.** Widgets run in a sandboxed iframe
   (`sandbox="allow-scripts"`, **never** `allow-same-origin`). Host ↔ widget
   communication is a typed `postMessage` protocol with strict origin/source
   guards. No widget can ever touch app cookies, storage, tokens, or the
   parent DOM. The existing M7-11 host already enforces this — the framework
   inherits.
2. **Configure, don't code.** The 90% path is: pick a widget from a registry,
   fill a form generated from its JSON Schema. Writing code is only for
   *building a new widget kind*, not for *using one*.
3. **DX is the product, too.** A first-time widget author should ship a
   working widget in **< 30 minutes** with: one `defineWidget()` call, a
   JSON Schema, and a dev playground that hot-reloads. Anything that gets
   between the author and `npm run widget:dev <name>` is a defect.
4. **One file per widget kind.** A widget kind is a self-contained module:
   one `index.tsx` calling `defineWidget()`, one `params.schema.json`. No
   separate config registrations, no string IDs duplicated across the repo.
5. **Reuse the engine we already have.** Widgets bind to the existing
   per-student **variable substitution** (`{{var}}`) and, when they produce
   an answer, feed the existing **per-subpart grader**. No parallel paths.
6. **Explanatory *or* answer-producing.** A widget is either (a) *explanatory*
   (builds intuition; no answer — the thermo sim today), or (b)
   *answer-producing* (the widget **is** the input). Both supported by the
   same runtime and the same SDK.
7. **First-party widgets are trusted code; the escape hatch stays sandboxed.**
   Registry widgets live in the repo, are code-reviewed, and ship in a
   dedicated runtime bundle. The "custom HTML" path (legacy thermo today)
   remains sandboxed *and* review-gated — exception, not rule.
8. **Versioned.** Each widget kind is versioned; a question pins a version
   so content never breaks when a widget evolves.
9. **Brand-native inside the sandbox.** Widgets pull V2 tokens (`brand-600`
   = `#FF6F00`, Fraunces+Inter, warm `ink`) via a shared `widget-runtime.css`
   so they read as one product, not a third-party embed.

---

## C. Architecture

```
┌─────────────────────────── App (parent origin) ───────────────────────────┐
│  QuestionCard / CreateQuestionPage                                         │
│    └── <InteractiveWidget kind config variables imageBase />               │
│          renders ↓                                                         │
│        <iframe sandbox="allow-scripts"                                     │
│                srcDoc={runtimeBundle + boot(kind, config)}>                │
│              ▲   │  postMessage protocol (typed, source-guarded)            │
│   init{kind,config,variables,imageBase} │ ready / resize{h} / value{v} /   │
│                                          │ error{msg}                       │
└──────────────────────────────────────────┼────────────────────────────────┘
                                            │  (opaque origin)
                ┌───────────────────────────▼───────────────────────────┐
                │  Widget runtime bundle (built once, served as srcdoc)  │
                │    registry[kind] → defineWidget({…}).render(…)        │
                │    @os/widget-sdk: useVariables, reportValue,          │
                │                    requestResize, onConfigChange       │
                │    widget-runtime.css: V2 brand tokens                 │
                └────────────────────────────────────────────────────────┘
```

**Layers:**

1. **Data.** `QuestionSubpart` gains `widget_kind` (registry key, nullable)
   and `widget_config` (JSON, validated against the widget's `params.schema`).
   The M7-11 `interactive_html` field remains *only* as the legacy/escape-
   hatch path; new content uses `widget_kind` + `widget_config`.
2. **Registry (frontend).** `frontend_modern/src/widgets/<kind>/`:
   - `index.tsx` — one `defineWidget({ id, version, meta, schema, render })` call.
   - `params.schema.json` — JSON Schema for the config form.
   - `playground.tsx` — a 1-line hookup of the widget into the local dev shell
     so `npm run widget:dev <kind>` boots a hot-reloading sandbox.
   - `README.md` — optional widget-specific notes; meta from `defineWidget`
     covers most of it.
   A central `registry.ts` lazy-loads each module by kind.
3. **Runtime + SDK.** A tiny typed `@os/widget-sdk` (lives at
   `frontend_modern/src/widgets/_sdk/` initially; can graduate to a package
   later) wraps the `postMessage` plumbing. Widget code only sees React/TS
   and SDK hooks — never `window.postMessage`.
4. **Authoring UX.** `CreateQuestionPage` gets an "Add interactive widget"
   panel: a gallery (thumbnails from `meta`), an auto-generated config form
   from `params.schema`, a **live preview** rendered through the same sandbox
   host, and variable binding so config fields can reference question
   variables.
5. **Grading.** Answer-producing widgets call `reportValue(answer)`; the host
   marshals it into `Submission.answers[subpart_id]`, graded by the existing
   per-subpart grader. No new grading path.

---

## D. Backlog — IW-1 → IW-8 (each ≈ one reviewable PR / batch item)

Routines (plan + execute) draw from this list. Increments are **PR-sized**
and built **lowest-risk-first**. The plan agent picks the top unblocked
increment(s) and breaks them into the day's batch.

### IW-1 — Runtime + SDK skeleton  *(do first; foundation)*
Convert the M7-11 `InteractiveWidget` host into a reusable runtime.

- **Files:**
  - `frontend_modern/src/widgets/_sdk/protocol.ts` — typed message union
    (`init` / `ready` / `resize` / `value` / `error`), with TypeScript helpers
    for both sides.
  - `frontend_modern/src/widgets/_sdk/host.ts` — host-side: builds the
    sandbox srcdoc, posts `init`, listens for `ready` / `resize` / `value`,
    enforces `event.source === iframe.contentWindow` (no origin trust).
  - `frontend_modern/src/widgets/_sdk/runtime.ts` — runtime-side (loaded
    inside the iframe): a `mountWidget(kind, mountNode)` boot + the public
    `useVariables` / `reportValue` / `requestResize` hooks.
  - `frontend_modern/src/widgets/registry.ts` — empty barrel for now;
    populated in IW-2.
  - Rewire `src/shared/ui/InteractiveWidget.tsx` to call into
    `_sdk/host.ts` so the existing M7-11 path still works (no regression).
  - One **hello-widget** (`src/widgets/_hello/`) — literally renders
    "Widget runtime alive · kind = {kind}" inside the sandbox. Proves the
    loop end-to-end.
- **DoD:**
  - A demo route (or `/design` extension) renders the hello-widget in a
    sandbox; auto-height works; vitest + Playwright assertions cover sandbox
    attrs + `init`→`ready` handshake.
  - Existing M7-11 thermo question (`44/22`) still renders correctly through
    the legacy `interactive_html` path — no regression.

### IW-2 — `defineWidget()` SDK + reference widget = `thermo-piston`
Prove the API by re-implementing the legacy Thermodynamics sim as a
first-class React widget — **no jQuery, no bespoke HTML**.

- **Files:**
  - `frontend_modern/src/widgets/_sdk/defineWidget.ts` — the factory:
    `defineWidget<TConfig, TAnswer>({ id, version, meta, schema, render }): WidgetModule`.
  - `frontend_modern/src/widgets/thermo-piston/` — `index.tsx` (the React
    component using SDK hooks), `params.schema.json` (initial volume,
    max heat, etc.), `README.md` (anatomy notes).
  - `registry.ts` — register `thermo-piston`.
  - **Migration plan written but not run yet** (the data flip happens in
    IW-3).
- **DoD:** A standalone showcase route renders the thermo-piston widget;
  slider, piston, ΔU readout all work; values substitute through
  `useVariables`. The "anatomy of a widget" guide is born from this PR
  (lives next to the source as a README excerpt).

### IW-3 — Data model + serializer
- **Files:**
  - `backend/openshiksha/apps/core/models.py` — add `widget_kind` (CharField,
    null=True) + `widget_config` (JSONField, default=dict) on `QuestionSubpart`.
  - Migration + admin display.
  - Serializer exposure on both the teacher and student serializers (the
    student serializer already substitutes variables — the host applies them
    to `widget_config` before posting `init`).
  - JSON Schema validation on save (Pydantic or jsonschema lib — reuse what's
    already in `requirements.txt`).
  - One-shot management command `migrate_legacy_thermo_widget` that maps the
    thermo question's `interactive_html` to `(widget_kind='thermo-piston',
    widget_config=<derived>)`.
- **DoD:** Migration applied; a question can carry a widget by kind+config;
  API returns it; invalid config rejected with a clear error; the thermo
  question now renders via the registry path (legacy `interactive_html` path
  still works for any other question that needs it).

### IW-4 — Answer-producing widgets
- **Files:**
  - SDK `reportValue(answer)` hook wired through the host into the
    submission flow.
  - `src/widgets/number-line/` — drag a point on a number line to mark a
    value; reports a numeric answer.
  - `params.schema.json` (range, step, target), schema validation, golden
    test.
- **DoD:** A student drags the point, the value posts into
  `Submission.answers[subpart_id]`, the existing numeric grader marks it
  correct/incorrect. Explanatory widgets (thermo) still work with no
  `reportValue` call.

### IW-5 — Authoring UX in `CreateQuestionPage`
- **Files:**
  - `frontend_modern/src/features/teacher/WidgetGalleryPanel.tsx` — modal
    that lists registry widgets (thumbnail + meta), preview on hover.
  - `frontend_modern/src/features/teacher/WidgetConfigForm.tsx` — renders a
    form from a widget's JSON Schema (use `@rjsf/core` or hand-roll something
    minimal — decide in the plan PR).
  - "Add interactive widget" button next to the subpart panel; live preview
    panel reuses the same `<InteractiveWidget>` host.
  - Variable-binding affordance (a field can be `"{{a}}"` rather than a
    literal number).
- **DoD:** A teacher creates a question with the thermo or number-line
  widget end-to-end through the UI, with **no code** and no JSON editing;
  preview matches student render.

### IW-6 — Library expansion (≥ 3 more widgets)
- **Files:**
  - `src/widgets/function-plotter/` — input parameters (a, b, c, …), plot
    a function over a range. Uses an existing chart lib (Recharts /
    `chartjs` — decide in the plan PR; prefer keeping bundle small).
  - `src/widgets/fraction-bar/` — drag dividers to split a bar into N equal
    parts. Answer-producing.
  - `src/widgets/circuit-builder/` (stretch, or alternative) — connect a
    battery → resistor → bulb; the bulb lights when complete.
- **DoD:** Each ships as a registry module + schema + thumbnail + showcase
  entry + golden test. "How to build a widget" guide updated with one of
  them as a worked example.

### IW-7 — Custom-HTML escape hatch (sandboxed)
- **Files:**
  - `src/widgets/_custom-html/` — a registry widget whose `params.schema`
    has a single `html` string field; renders the value through the same
    sandbox host with the same vendor head.
  - Review flag on the question (admin-set; not exposed to regular
    teachers in the gallery).
- **DoD:** The legacy thermo HTML, the new `thermo-piston`, *and* any
  future bespoke-HTML widget all flow through the same `<InteractiveWidget>`
  host. The `interactive_html` field can then be marked deprecated.

### IW-8 — Newcomer kit (DX seal of approval)
This is what makes the initiative "feel natural and attract newer people."

- **Files:**
  - `frontend_modern/scripts/create-widget.mjs` — CLI invoked as
    `npm run widget:new <kind-slug>` that scaffolds:
    `src/widgets/<kind>/{index.tsx, params.schema.json, playground.tsx,
    README.md}` from a tiny template; registers it in `registry.ts`.
  - `frontend_modern/src/widgets/_playground/` — a dev route at `/widgets/dev`
    that loads a chosen widget into the sandbox host with a JSON config
    editor on the side. Hot-reloads.
  - `docs/widgets/build-your-first-widget.md` — a 10-minute tutorial: scaffold,
    write `render`, define schema, see it in the playground, add to a
    question. Worked from the simplest possible widget.
  - `docs/widgets/anatomy.md` — the canonical reference for the
    `defineWidget()` API + SDK hooks + protocol.
- **DoD:** A reviewer running `npm run widget:new color-picker` followed by
  the tutorial ships a working widget in < 30 min on a clean checkout. Each
  reviewer-tested loop tightens the docs.

**Suggested order:** IW-1 → IW-2 → IW-3 → IW-4 ∥ IW-5 → IW-6 → IW-7 → IW-8.
IW-8 can also be split — `npm run widget:new` is a great early ship (right
after IW-2) so the DX wins compound while later widgets are being built.

---

## E. Continuous Improvement list (the compounding step)

Pick one small hardening task whenever advancing this initiative:

- Tighten the `postMessage` protocol types / add an origin+schema guard on
  every message.
- Add an SRI hash / vendor-pin for any third-party lib a widget loads.
- Add a widget to the visual showcase / `/design` gallery.
- Add an a11y pass to a widget (keyboard control for the slider/piston,
  ARIA labels, screen-reader text for state changes).
- Add a `prefers-reduced-motion` path to any animated widget.
- Add a golden screenshot to the M6-03 visual-regression set (once baselines
  are seeded — see #207).
- Improve the `defineWidget()` types or the dev playground polish.
- Document one more entry in "anatomy of a widget."

---

## F. Cross-cutting Definition of Done (North Star reached)

- A new widget kind can be added as a **single self-contained file +
  schema** via `defineWidget()`, with **zero framework changes**.
- `npm run widget:new <kind>` scaffolds it in seconds; `npm run widget:dev
  <kind>` boots it in a hot-reloading sandbox.
- A teacher can attach an existing widget to a question through the UI
  without writing code.
- Every widget renders in a sandbox with no `allow-same-origin`; the app
  origin is never reachable from widget code.
- Answer-producing widgets grade through the existing per-subpart grader.
- The legacy thermo sim runs as a first-class registry widget (no bespoke
  HTML).
- A "How to build a widget" tutorial + ≥ 5 reference widgets ship (hello,
  thermo-piston, number-line, function-plotter, fraction-bar; circuit-builder
  is a bonus).

---

## G. Out of scope

- A visual drag-and-drop *widget builder* (compose SVG/logic in-app) — far
  future; the registry + schema model is the deliverable, not a no-code
  builder.
- Real-time multiplayer/collaborative widgets (separate Channels concern).
- Importing third-party interactive content (PhET, GeoGebra) — could be a
  future widget kind via an iframe-embed widget, but not part of the core
  framework.

---

## H. Relationship to other initiatives

- **Cabinet Data Fidelity → M7-11** is the *seed*. The host
  (`InteractiveWidget.tsx`) shipped in #132 as a generic sandbox primitive
  precisely so IW-1 hardens it into the reusable runtime, not throws it
  away. The thermo question is the migration target for IW-2 → IW-3.
- **V2 "Chalk & Unlock"** owns the visual language. Widgets must use V2
  tokens inside the sandbox (`widget-runtime.css` exports `brand-600`,
  `ink-*`, Fraunces+Inter). The V2 initiative is now effectively closed
  (see [STATUS.md](STATUS.md)) so this is the new top priority.
- **M6-03 visual-regression set** (#207) — every shipped widget gets a
  snapshot in the regression set once Linux baselines are seeded.

---

## I. Progress Ledger

| Date | Increment | PR | Hardening / learning |
|---|---|---|---|
| 2026-06-04 | Initiative promoted from ⚪ Proposed to 🟢 Active; full IW-1…IW-8 backlog written; DX-first principle added. | _(this docs PR)_ | Routine handoff documented (plan reads STATUS → reads this doc → batches IW-1 first). M7-11 host stays as the legacy/escape-hatch path through IW-7. |
