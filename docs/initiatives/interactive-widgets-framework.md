# Interactive Widgets Framework — Initiative (Proposed)

> **North Star:** Authoring a new interactive educational widget (a piston
> simulation, a number line, a function plotter, a circuit builder) should be
> as easy as picking it from a gallery and filling in a form — and rendering
> one should be **safe by construction**, never a raw-`<script>` XSS hole.
>
> **Status:** ⚪ Proposed (not yet scoped onto the active board). Promote when
> Cabinet Data Fidelity closes and the M7-11 sandbox primitive (its one-off
> predecessor) is in place.

**Last updated:** 2026-06-01

---

## A. Why this initiative exists

The legacy platform marketed *"educational games, interactive widgets"* and
shipped exactly one true example: the Class 11 Thermodynamics piston/First-Law
simulation (`openshiksha-cabinet/questions/raw/1/1/11/3/44/22.json`). It was
authored as **bespoke raw HTML + SVG + inline jQuery `<script>`** embedded in the
question content. That approach is a dead end for three reasons:

1. **Insecure.** Raw author `<script>` injected into the app DOM is the exact XSS
   risk DOMPurify exists to block. The modern renderer correctly strips it — which
   *silently kills the widget*.
2. **Not reusable.** Every widget re-hand-wrote its own SVG, slider, and event
   loop. There is no shared slider, no shared plot, no shared anything. A second
   widget meant starting from zero.
3. **Unauthorable.** Only someone who could hand-write SVG + jQuery could make
   one. Teachers and content authors had no path to create interactive content.

**M7-11** (in the Cabinet Data Fidelity initiative) rescues the *one* legacy
widget by preserving its HTML and rendering it in a sandboxed iframe. This
initiative is the **forward-looking** sequel: turn that one-off rescue into a
**framework** where interactive widgets are first-class, reusable, safe, and
easy to author — so the platform can actually deliver on the "interactive
learning" promise at scale.

---

## B. Design principles

- **Safe by construction.** Widgets run in a sandboxed iframe
  (`sandbox="allow-scripts"`, **never** `allow-same-origin`). The host app and the
  widget communicate only through a typed `postMessage` protocol. No widget can
  ever touch app cookies, storage, tokens, or the parent DOM.
- **Configure, don't code.** The common path is: pick a widget from a registry,
  fill a form generated from the widget's parameter schema. Writing code is only
  for *building a new widget kind*, not for *using one*.
- **First-party widgets are trusted code.** Registry widgets live in the repo,
  are code-reviewed, and are built into a dedicated runtime bundle. This is
  categorically safer than arbitrary author HTML — the untrusted path (a
  "custom HTML" escape hatch) stays sandboxed and review-gated, and is the
  exception, not the rule.
- **Reuse the engine we already have.** Widgets bind to the existing per-student
  **variable substitution** (`_{k}_` / `{{k}}`) and, when they produce an answer,
  feed the existing **per-subpart grader** — no parallel grading path.
- **Explanatory or answer-producing.** A widget is either (a) *explanatory*
  (builds intuition; no answer — the thermo sim today), or (b) *answer-producing*
  (the widget **is** the input: "drag the point to x = 3", "set the piston to do
  50 J of work"). Both are supported by the same runtime.
- **Versioned.** Each widget kind is versioned; a question pins a version so
  content never breaks when a widget evolves.

---

## C. Architecture

```
┌─────────────────────────── App (parent origin) ───────────────────────────┐
│  QuestionCard / CreateQuestionPage                                         │
│    └── <InteractiveWidget type config variables imageBase />               │
│          renders ↓                                                         │
│        <iframe sandbox="allow-scripts" src="/widget-runtime#<type>">       │
│              ▲   │  postMessage protocol (typed)                            │
│   init{type,config,variables,imageBase} │   ▼ ready / resize{h} / value{v} │
└──────────────────────────────────────────┼────────────────────────────────┘
                                            │  (isolated origin / srcdoc)
                ┌───────────────────────────▼───────────────────────────┐
                │   Widget runtime bundle                                │
                │     registry[type] → <ThermoPiston cfg vars/>          │
                │     @os/widget-sdk: onInit, reportValue, requestResize │
                └────────────────────────────────────────────────────────┘
```

**Layers:**

1. **Data.** `QuestionSubpart` gains `widget_type` (registry key, nullable) and
   `widget_config` (JSON, validated against that widget's param schema). The
   M7-11 `interactive_html` field remains *only* as the legacy/escape-hatch path.
2. **Registry (frontend).** `frontend_modern/src/widgets/<type>/` — each widget is
   a self-contained module: a React/TS component built for the runtime, a
   JSON-Schema `params.schema.json`, and metadata (title, description, thumbnail,
   suggested subjects/standards). A central `registry.ts` maps `widget_type` →
   module. Widgets are built into a separate Vite entry (`widget-runtime`) so they
   never share a bundle/origin with the app.
3. **Runtime + protocol.** The `InteractiveWidget` host posts
   `init{ type, config, variables, imageBase }`; the widget replies `ready`,
   `resize{ height }`, and optionally `value{ answer }`. A tiny typed
   `@os/widget-sdk` (`onInit`, `getVariable`, `reportValue`, `requestResize`)
   hides the `postMessage` plumbing so widget authors write only widget logic.
4. **Authoring UX.** `CreateQuestionPage` gets an "Add interactive widget" panel:
   a gallery of registry widgets (thumbnails), a config form auto-generated from
   the chosen widget's JSON Schema, a **live preview** rendered through the same
   sandbox host, and variable binding (config fields can reference question
   variables so the widget reacts to per-student values).
5. **Grading.** Answer-producing widgets report a value via the SDK; it is stored
   as the submission answer and graded by the existing per-subpart grader (numeric
   / multi-select / etc.). No new grading path.

---

## D. Backlog (each ≈ one reviewable PR/increment)

| ID | Increment | Definition of Done | Depends on |
|---|---|---|---|
| **IW-1** | **Runtime + protocol skeleton.** Sandboxed iframe host (`InteractiveWidget`), `widget-runtime` Vite entry, typed `@os/widget-sdk`, `init`/`ready`/`resize` messages, auto-height. Ship a trivial "hello widget" to prove the loop. | A demo route renders a sandboxed widget that resizes itself; no `allow-same-origin`; RTL test asserts the sandbox attrs + message handshake. | M7-11b (sandbox primitive) |
| **IW-2** | **Registry + reference widget = `thermo-piston`.** Re-implement the legacy Thermodynamics sim as the first first-class registry widget (React/SVG component, no jQuery), driven by `widget_config` + variable binding. Retire its bespoke `interactive_html`. | Q `44/22` renders via the registry, slider + piston work, live ΔU updates, values substitute per student. Reference doc "anatomy of a widget" written. | IW-1 |
| **IW-3** | **Data model + serializer.** Add `widget_type` + `widget_config` to `QuestionSubpart`, JSON-Schema validation on save, serializer exposure, importer maps the legacy thermo question onto the registry widget. | Migration + backfill; a question can carry a widget by type+config; API returns it; invalid config rejected with a clear error. | IW-2 |
| **IW-4** | **Answer-producing widgets.** Wire `reportValue` into the submission/grading flow so a widget can *be* the input. Add one answer-producing reference widget (e.g. `number-line-point`). | A student drags a point, the value is submitted and graded by the existing grader; explanatory widgets still work with no answer. | IW-3 |
| **IW-5** | **Authoring UX.** "Add interactive widget" panel in `CreateQuestionPage`: gallery + schema-driven config form + live sandboxed preview + variable binding. | A teacher creates a question with a widget end-to-end through the UI, no code; preview matches student render. | IW-3 |
| **IW-6** | **Widget library expansion.** Add 2–3 high-value widgets (e.g. `function-plotter`, `circuit-builder`, `fraction-bar`) using only the SDK + registry — no framework changes. | Each ships as a registry module + schema + thumbnail + showcase entry; "How to build a widget" guide updated. | IW-2 |
| **IW-7** | **Custom-HTML escape hatch (sandboxed).** A reviewed, flagged path for power users to author raw HTML/JS widgets, still inside the sandbox, for cases the registry doesn't cover. | Authoring it requires a review flag; it renders only in the sandbox; never reaches the app DOM. Replaces the M7-11 legacy path generically. | IW-1 |

**Suggested order:** IW-1 → IW-2 → IW-3 → (IW-4 ∥ IW-5) → IW-6 → IW-7. IW-1/IW-2
prove the framework on the real legacy widget before any authoring or data-model
investment.

---

## E. Continuous Improvement list (the compounding step)

Pick one small hardening task whenever advancing this initiative:

- Tighten the `postMessage` protocol types / add an origin+schema guard on every
  message.
- Add an SRI hash / vendor-pin for any third-party lib a widget loads.
- Add a widget to the visual showcase / Storybook-style gallery.
- Add an a11y pass to a widget (keyboard control for the slider/piston, ARIA).
- Add a `prefers-reduced-motion` path to any animated widget.
- Document one more entry in "anatomy of a widget."

---

## F. Cross-cutting Definition of Done (North Star reached)

- A new widget kind can be added as a single self-contained registry module
  (component + schema + metadata) with **zero** framework changes.
- A teacher can attach an existing widget to a question through the UI without
  writing code.
- Every widget renders in a sandbox with no `allow-same-origin`; the app origin is
  never reachable from widget code.
- Answer-producing widgets grade through the existing per-subpart grader.
- The legacy thermo sim runs as a first-class registry widget (no bespoke HTML).
- A "How to build a widget" guide + ≥4 reference widgets exist.

---

## G. Out of scope

- A visual drag-and-drop *widget builder* (compose SVG/logic in-app) — far future;
  the registry+schema model is the deliverable, not a no-code builder.
- Real-time multiplayer/collaborative widgets (separate Channels concern).
- Importing third-party interactive content (PhET, GeoGebra) — could be a future
  widget kind via iframe embed, but not part of the core framework.

---

## H. Relationship to other initiatives

- **Cabinet Data Fidelity → M7-11** is the *seed*: it preserves + sandbox-renders
  the one legacy widget. This initiative generalises that into an authoring
  framework. M7-11 should be built so its sandbox host is the thing IW-1
  hardens into the reusable runtime — not a throwaway.
- **V2 "Chalk & Unlock"** owns the visual language; widgets must use V2 tokens
  (orange `#FF6F00`, Fraunces+Inter, warm paper/`ink`) inside the sandbox.

---

## I. Progress Ledger

| Date | Increment | PR | One-line learning |
|---|---|---|---|
| _(none yet — proposed)_ | | | |
