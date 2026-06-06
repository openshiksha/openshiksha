# Interactive Widgets Framework — Initiative

> **North Star:** Three tiers of authoring, one runtime:
>
> 1. **Use a widget** (every teacher): pick from a gallery, fill a form.
> 2. **Compose a widget** (any teacher, in-app **Widget Studio**): drag a
>    slider, a plot, and a value readout onto a canvas, wire them with a
>    formula — your own widget, saved to your school, no code.
> 3. **Build a widget kind** (contributor): one `defineWidget(...)` file +
>    a JSON Schema, hot-reloading in a dev playground, ready in < 30 min.
>
> Every tier renders through the **same sandboxed iframe** — safe by
> construction, never a raw-`<script>` XSS hole.
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
safe, **and a joy to author at every skill level** — so the platform can
actually deliver on the "interactive learning" promise at scale, *and*
attract both contributors who build new widget kinds and teachers who want
to compose their own interactive content.

**Crucially, "authorable" means *teachers*, not just contributors with repo
access.** A maths teacher who wants a slider that drives a chart should be
able to build that themselves, in the app, without writing code — and
publish it to their school. That's what the **Widget Studio** (Tier 2 above)
delivers, alongside the contributor-facing SDK (Tier 3).

---

## B. Design principles

1. **Safe by construction.** Widgets run in a sandboxed iframe
   (`sandbox="allow-scripts"`, **never** `allow-same-origin`). Host ↔ widget
   communication is a typed `postMessage` protocol with strict origin/source
   guards. No widget can ever touch app cookies, storage, tokens, or the
   parent DOM. The existing M7-11 host already enforces this — the framework
   inherits.
2. **Three tiers of authoring, one runtime.** Every authored widget — whether
   a teacher dropped a slider on a Studio canvas, a teacher configured a
   first-party `function-plotter`, or a contributor wrote a `defineWidget()`
   module — ships through the **same** sandboxed `<InteractiveWidget>` host.
   The tiers differ only in *who can author* and *how the widget definition
   is produced*, never in the security boundary or the render path.
3. **Configure / Compose / Code — pick the right tier per task.**
   - *Tier 1 — Configure (every teacher):* pick a registry widget, fill a
     form generated from its JSON Schema. **The 90% path.**
   - *Tier 2 — Compose (any teacher, in-app Widget Studio):* drag
     primitives (slider / input / plot / value readout / image / formula)
     onto a canvas, wire bindings, save. The Studio is a **constrained
     visual builder** that emits the same `widget_config` JSON other widgets
     use — no user code is ever executed; the studio scene is data.
   - *Tier 3 — Code (contributor):* one `defineWidget()` file + JSON Schema
     in `src/widgets/<kind>/`. Reserved for genuinely-novel widget kinds
     (thermo piston, circuit builder) that the Studio's primitives can't
     express.
4. **DX is the product, too.** A first-time contributor (Tier 3) should ship
   a working widget in **< 30 minutes** via `npm run widget:new <kind>` +
   `npm run widget:dev <kind>`. A first-time teacher (Tier 2) should
   compose their first widget in the Studio in **< 5 minutes** — the same
   "feels natural" bar, just lower-friction.
5. **One file per widget kind** (Tier 3). A widget kind is a self-contained
   module: one `index.tsx` calling `defineWidget()`, one
   `params.schema.json`. No separate config registrations, no string IDs
   duplicated across the repo.
6. **The Studio composes, never executes.** Tier 2 scenes are pure data: a
   list of primitive instances + a list of bindings + simple formula
   expressions evaluated by the existing `safe_eval_expr` engine (same one
   the cabinet importer + croupier already trust). **The Studio never
   `eval()`s teacher code, never `<script>`s a teacher string, never
   reaches `Function(...)`.** A scene runs by the runtime *interpreting*
   the data inside the same sandbox every other widget uses.
7. **Trust scope matches authoring scope.** A Tier 1 use of a registry
   widget is allowed for any teacher. A Tier 2 Studio widget is **scoped
   to its school by default** (the school's teachers can pick it from the
   gallery; visibility never crosses schools without an admin opt-in).
   A Tier 3 widget kind requires a repo PR (code review). The "custom
   HTML" escape hatch (legacy thermo) is admin-flagged per question and
   sandboxed.
8. **Reuse the engine we already have.** Widgets bind to the existing
   per-student **variable substitution** (`{{var}}`) and, when they produce
   an answer, feed the existing **per-subpart grader**. No parallel paths.
9. **Explanatory *or* answer-producing.** A widget is either (a) *explanatory*
   (builds intuition; no answer — the thermo sim today), or (b)
   *answer-producing* (the widget **is** the input). Both supported by the
   same runtime and the same SDK — and both kinds are buildable in the
   Studio as well as in code.
10. **Versioned.** Each widget kind is versioned; a question pins a version
    so content never breaks when a widget evolves. Studio scenes carry a
    schema version too, so a future Studio runtime can migrate older scenes.
11. **Brand-native inside the sandbox.** Widgets pull V2 tokens (`brand-600`
    = `#FF6F00`, Fraunces+Inter, warm `ink`) via a shared
    `widget-runtime.css` so they read as one product, not a third-party
    embed.

---

## C. Architecture

```
┌─────────────────────────── App (parent origin) ───────────────────────────┐
│  QuestionCard / CreateQuestionPage / WidgetStudio                          │
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
                │    +  kind = "studio-scene"  →  StudioRuntime(config)  │
                │       interprets data: primitives + bindings + formula │
                │    @os/widget-sdk: useVariables, reportValue,          │
                │                    requestResize, onConfigChange       │
                │    widget-runtime.css: V2 brand tokens                 │
                └────────────────────────────────────────────────────────┘
```

The **`studio-scene` kind** is just one more registry entry — its
`widget_config` happens to be a Studio scene rather than a hand-written
config blob. To the host, runtime, sandbox, grader, and database, it's
indistinguishable from a Tier-1 widget. That's how three authoring tiers
collapse to one render path.

**Layers:**

1. **Data — questions.** `QuestionSubpart` gains `widget_kind` (registry
   key, nullable) and `widget_config` (JSON, validated against the widget's
   `params.schema`). The M7-11 `interactive_html` field remains *only* as
   the legacy/escape-hatch path; new content uses `widget_kind` +
   `widget_config`.
2. **Data — Studio widgets.** A new `TeacherWidget` model stores
   Studio-built widgets: `{ id, name, description, school, created_by,
   visibility, scene_version, scene }`. A teacher attaching a Studio
   widget to a question writes `widget_kind = "studio-scene"` +
   `widget_config = { teacher_widget_id }` on the subpart (the runtime
   then loads the named scene). This indirection lets the teacher fix
   typos in one place and update every question that references it.
3. **Registry (frontend).** `frontend_modern/src/widgets/<kind>/`:
   - `index.tsx` — one `defineWidget({ id, version, meta, schema, render })` call.
   - `params.schema.json` — JSON Schema for the config form.
   - `playground.tsx` — a 1-line hookup of the widget into the local dev shell
     so `npm run widget:dev <kind>` boots a hot-reloading sandbox.
   - `README.md` — optional widget-specific notes; meta from `defineWidget`
     covers most of it.
   A central `registry.ts` lazy-loads each module by kind. The
   `studio-scene` kind lives here too, as a built-in.
4. **Runtime + SDK.** A tiny typed `@os/widget-sdk` (lives at
   `frontend_modern/src/widgets/_sdk/` initially; can graduate to a package
   later) wraps the `postMessage` plumbing. Widget code only sees React/TS
   and SDK hooks — never `window.postMessage`.
5. **Studio runtime** (a thin sibling of the contributor SDK). Lives at
   `src/widgets/studio-scene/` as the `studio-scene` widget. Given a scene,
   it instantiates the primitives (e.g. `<StudioSlider>`, `<StudioPlot>`,
   `<StudioReadout>`), wires bindings via React state, and evaluates
   formula nodes through the same `safe_eval_expr` used by the grader.
   Primitives are a fixed, audited set in the repo — the Studio is *not*
   an arbitrary code runner.
6. **Authoring UX.** `CreateQuestionPage` gets an "Add interactive widget"
   panel that lists the registry gallery **plus the school's Studio
   widgets**. A dedicated **`/teacher/widgets` Studio route** lets a
   teacher create / edit / preview / save a Studio widget; the same UI
   handles the in-line "Build new widget" flow from `CreateQuestionPage`.
7. **Grading.** Answer-producing widgets call `reportValue(answer)`; the host
   marshals it into `Submission.answers[subpart_id]`, graded by the existing
   per-subpart grader. No new grading path — Studio widgets that include an
   "answer" primitive participate in grading the same way.

---

## D. Backlog — IW-1 → IW-11 (each ≈ one reviewable PR / batch item)

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

### IW-9 — Widget Studio runtime + primitives (Tier 2 foundation)
The data + render half of teacher-authored widgets — no UI yet. Ships the
`studio-scene` widget kind, the primitives, and the formula evaluator so
**a scene authored by hand in JSON renders correctly through the sandbox**.
The visual builder lands in IW-10 on top of this.

- **Files:**
  - `frontend_modern/src/widgets/studio-scene/` — a registry widget whose
    `params.schema` is the Studio scene schema. Its `render` builds a tree
    of primitives from the scene + wires bindings.
  - `frontend_modern/src/widgets/studio-scene/primitives/` —
    `Slider.tsx`, `NumberInput.tsx`, `Dropdown.tsx`, `Label.tsx`,
    `Readout.tsx`, `Plot.tsx`, `Image.tsx`, `Formula.ts` (data
    transformer, not a component). Each primitive has a typed config and
    one well-defined output value other primitives can bind to.
  - `frontend_modern/src/widgets/studio-scene/formula.ts` — thin wrapper
    over the existing `safe_eval_expr` engine (the croupier / cabinet
    code already implements this safely on the backend; mirror it on
    the runtime side here for client-side evaluation as the teacher
    drags sliders).
  - `frontend_modern/src/widgets/studio-scene/scene.schema.json` — the
    JSON Schema for a scene: `{ schema_version, primitives: [...],
    bindings: [...], answer?: <binding-path> }`.
  - **Backend:** new `TeacherWidget` model (`apps/core/models.py`):
    `id`, `name`, `description`, `school` FK (null=True for personal),
    `created_by` FK, `visibility` (personal / school / pending-review),
    `scene_version`, `scene` (JSONField, validated). Migration + admin.
    DRF endpoints `GET/POST/PATCH /teacher-widgets/` scoped to
    `request.user.school`. Serializer returns the scene to the host so
    `widget_config = { teacher_widget_id }` can be resolved.
- **DoD:**
  - A hand-written scene JSON (one slider + one Plot + one Formula
    binding the slider value into the plot's `x` series) renders
    correctly through the sandbox.
  - The schema-validation step rejects unknown primitive types and
    invalid bindings with a clear error.
  - `TeacherWidget` permissions: a teacher only sees their own + their
    school's; cross-school access requires an explicit visibility flag.
  - Vitest coverage of `formula.ts` for at least the cabinet's existing
    safe-eval test vectors (no eval / Function / proto access).

### IW-10 — Widget Studio UI (Tier 2 visual builder)
The teacher-facing canvas. Lands the **< 5-min "compose your first widget"**
experience the North Star promises.

- **Files:**
  - `frontend_modern/src/features/teacher/widget-studio/` — a new feature
    folder owning the Studio.
    - `WidgetStudioPage.tsx` at route `/teacher/widgets/:id?` (new ↔ edit
      same component); lists existing TeacherWidgets in a sidebar.
    - `StudioCanvas.tsx` — the drag surface: primitives panel on the left
      (slider / input / dropdown / label / readout / plot / image / formula),
      a grid canvas in the centre, a property inspector on the right.
    - `StudioBindingEditor.tsx` — a visual "wire from slider.value to
      plot.x" affordance (a select-from-list, not actual line-drawing on
      day one).
    - `StudioFormulaField.tsx` — a constrained expression input with
      autocomplete from in-scope primitive outputs + variable tokens.
    - `StudioPreviewPanel.tsx` — embeds `<InteractiveWidget kind="studio-scene"
      config={scene} />` next to the canvas so the teacher sees the live
      render. **Same sandbox the student will see.**
  - `frontend_modern/src/features/teacher/widget-studio/templates/` — three
    or four ready-made scenes the teacher can fork: "Slider drives a
    formula readout", "Two sliders + a plot", "Drag-to-mark-on-number-line",
    "Image with a hotspot". Picking a template is what makes < 5 minutes
    achievable.
  - "Add interactive widget" panel in `CreateQuestionPage` (built in IW-5)
    is updated to include the school's Studio widgets in the gallery.
- **DoD:**
  - A first-time teacher can: open `/teacher/widgets/new` → pick the
    "Slider + formula readout" template → change the formula to
    `2 * a + 1` → save with a name → attach it to a question subpart →
    students see the working widget. Stopwatch ≤ 5 min on a clean
    account.
  - The Studio never `eval()`s text; the only execution path is the
    audited `safe_eval_expr` already trusted by the cabinet.
  - A "share with my school" toggle in the save dialog publishes the
    widget to the gallery for other school teachers; default is personal.
  - A11y: every canvas action is also keyboard-reachable (add primitive
    via a `+ Primitive` menu; reorder with arrow keys); the binding
    editor is a labelled `<select>` group, not a mouse-only affordance.

### IW-11 — Studio polish + power features  *(optional, scope on demand)*
- A "test as student" mode that runs the Studio scene in the exact same
  sandbox path the student will hit, with variable substitution.
- Versioned scene history (autosaved drafts, "revert to last published").
- An admin-level "promote to first-party" path that copies a popular
  Studio scene into a contributor-coded Tier-3 widget via PR.
- An export-to-JSON / import-from-JSON button so teachers can swap scenes
  outside the app.

**Suggested order:** IW-1 → IW-2 → IW-3 → IW-4 ∥ IW-5 → IW-6 → IW-7 →
IW-8 → IW-9 → IW-10 → IW-11. `npm run widget:new` from IW-8 is a great
early ship (right after IW-2) so the DX wins compound while later widgets
are being built. IW-9 + IW-10 can also start once IW-3 (the data model)
lands — they don't have to wait for IW-7's escape hatch.

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

**Tier 1 — Configure**
- A teacher can attach an existing widget to a question through the UI
  without writing code.

**Tier 2 — Compose (Widget Studio)**
- A first-time teacher can compose, save, and attach their own widget in
  **< 5 min** from `/teacher/widgets/new`.
- Studio widgets are scoped to the teacher's school by default; cross-
  school sharing requires an explicit opt-in.
- The Studio never `eval()`s teacher text; the only execution path is the
  audited `safe_eval_expr` engine.

**Tier 3 — Code**
- A new widget kind can be added as a **single self-contained file +
  schema** via `defineWidget()`, with **zero framework changes**.
- `npm run widget:new <kind>` scaffolds it in seconds; `npm run widget:dev
  <kind>` boots it in a hot-reloading sandbox; a first-time contributor
  ships in **< 30 min** on a clean checkout.
- A "How to build a widget" tutorial + ≥ 5 reference widgets ship (hello,
  thermo-piston, number-line, function-plotter, fraction-bar; circuit-builder
  is a bonus).

**Cross-cutting**
- Every widget — Tier 1, 2, or 3 — renders in a sandbox with no
  `allow-same-origin`; the app origin is never reachable from widget code.
- Answer-producing widgets grade through the existing per-subpart grader,
  irrespective of tier.
- The legacy thermo sim runs as a first-class registry widget (no bespoke
  HTML), with the legacy `interactive_html` field marked deprecated.

---

## G. Out of scope

- **Arbitrary code execution by teachers.** The Studio is a *constrained
  composer over audited primitives*. A teacher cannot author a widget that
  runs raw JavaScript, only a scene the runtime interprets. If a use case
  needs arbitrary code, it graduates to a Tier-3 contributor PR.
- **Free-form SVG drawing in the Studio.** The primitives are a fixed,
  audited set (slider, input, plot, readout, image, formula, …). Adding a
  *new primitive* is a Tier-3 contributor PR, not a teacher action — same
  trust boundary as adding a new widget kind.
- **Real-time multiplayer / collaborative widgets** (separate Channels
  concern).
- **Importing third-party interactive content (PhET, GeoGebra)** — could be
  a future widget kind via an iframe-embed widget, but not part of the core
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
| 2026-06-05 | **IW-3a** — `widget_kind` + `widget_config` fields on `QuestionSubpart`; server-side `KNOWN_WIDGET_KINDS` registry + writable-serializer guard; admin + read/write serializer exposure; 10 backend tests. | #211 | Backend keystone shipped **independently of IW-1** so the data model is ready the moment IW-1 + IW-2 land. Per-kind JSON-Schema validation hangs off `apps/core/widgets.py` and arrives per widget. |
| 2026-06-05 | **IW-3b** — `migrate_legacy_thermo_widget` idempotent one-shot command + per-student `{{var}}` substitution into `widget_config` in the student serializer (reuses the croupier helper — no parallel substitution path). | #212 | Legacy thermo question now has a stamping path onto the kind-based runtime; widget configs share the croupier's token semantics so an authored `"{{a}}"` resolves the same way the question's body already does. |
| 2026-06-05 | **IW-9-backend** — `TeacherWidget` model + migration + admin (model-only slice; DRF endpoints deferred to IW-9 proper). | #213 | Shipped table-first so the Studio PR starts from "wire endpoints + UI" rather than "design the schema while shipping a visual builder". `scene` is pure data; the Studio composes, the runtime interprets — never `eval`. |
| 2026-06-05 | **IW-1a** — protocol types (`HostMessage = InitMessage`, `WidgetMessage = Ready \| Resize \| Value \| Error`) + narrow type guards + `WIDGET_PROTOCOL_VERSION` const; 10 vitest cases. | #214 | Pure types; zero runtime risk; pins the wire contract IW-1b (host) and IW-1c (runtime) both import. Origin check is deliberately *not* in the protocol — that lives in `host.ts` because `allow-scripts` sandboxes have `event.origin === "null"`. |
| 2026-06-05 | **IW-1b** — `_sdk/host.ts` module (`buildLegacySrcDoc`, `buildHostSrcDoc`, `createHostBridge`) + `InteractiveWidget.tsx` rewired to delegate srcdoc + bridge through the SDK; 14 new vitest cases. | #215 | Legacy thermo path is byte-equivalent (legacy srcdoc string unchanged). New framework srcdoc bakes the `init` payload with `</script>` escaped to `<</script>` so authoring cannot break out of the boot script. Bridge enforces `event.source === iframe.contentWindow` *before* dispatching — the security boundary's primary identifier. |
| 2026-06-05 | **IW-1c** — `_sdk/defineWidget`, `_sdk/runtime` (sandbox boot), `widgets/registry.ts`, `_hello/` reference widget, `InteractiveWidget` extended with `kind`/`config` mode + V2-token shell, `/design` showcase, `widgets/README.md`; 12 new vitest cases. | #216 | Closes IW-1 — the loop renders end-to-end. Render source is `.toString()`'d at app-bundle time and inlined into the srcdoc; unknown kinds emit a typed `error` instead of silently no-op'ing. Vanilla DOM render for `_hello`. |
| 2026-06-05 | **IW-2** — `thermo-piston` widget (vanilla DOM/SVG, ~3 KB) + `params.schema.json` + widget README + `/design` showcase + IW-3b migration-command defaults updated to the real config schema; 8 new vitest cases. | #217 | First non-stub widget on the framework. Kinetic-theory particles vibrate with `ΔU = ΔQ − ΔW` (`requestAnimationFrame` loop, amplitude/speed/radius all scale with internal energy). Piston clamped (`PISTON_Y_MIN/MAX`) so it never dips below the cylinder floor; gas region floored at 36 px so particles always have room to jiggle. No jQuery, no Bootstrap glyphicons, no embedded `<script>` — ~280 KB of vendor head dropped vs. the legacy. |
| 2026-06-06 | **IW-8-early** — `npm run widget:new <kind>` scaffolder (`scripts/create-widget.mjs`) + `docs/widgets/anatomy.md` canonical SDK reference + `widgets/README.md` rewritten around the scaffolder + named `widget:new import/entry anchor` comments in `registry.ts`; 11 new vitest cases. | #218 | DX win the backlog said to ship right after IW-2. Adding a widget kind is now one command instead of copy-`_hello`-and-rename-three-things. The script validates the slug, refuses duplicates, prints the server-side `KNOWN_WIDGET_KINDS` reminder. `/widgets/dev` playground deliberately deferred to keep this PR atomic. |
| 2026-06-06 | **IW-7** — `custom-html` registry widget + `interactive_html` / `is_interactive` flagged DEPRECATED on `QuestionSubpart` (auto-migration 0020) + `/design` showcase proving inline scripts run inside the sandbox; 7 new vitest cases. | #219 | Closes the **Tier-3 contributor surface**. Every authoring path on the platform — first-party widget, Studio scene, scaffolded contributor widget, *and* one-off bespoke HTML — now flows through the same sandboxed `<InteractiveWidget>` host. The widget re-executes inline `<script>` tags after `innerHTML` insertion using the clone-and-replace pattern; `async = false` keeps multi-script load order intact for vendor head chains. Admin-only via `meta.title` until IW-5's gallery enforces it programmatically. |
| 2026-06-06 | **IW-4** — answer-producing widget plumbing (`InteractiveWidget.onValue` forwarding source-guarded `value` messages; `QuestionCard` hides typed input when `meta.answerProducing` and routes the widget's value into the answer state) + `number-line` widget (pointer events + `setPointerCapture` + keyboard a11y, no `reportValue` on mount); 10 new vitest cases. | #220 | First answer-producing widget on the framework. `number-line` snaps to step on every move so the reported value matches what the student sees under the point at all times; the grader receives whatever the student last saw. Explanatory widgets (`thermo-piston`, `custom-html`) keep the typed input and never trigger `onValue`. |
| 2026-06-06 | **IW-5** — `WidgetGalleryPanel` (schema-driven form + live preview) + `CreateQuestionPage` integration (Subpart draft carries `widget_kind` + `widget_config`; payload includes them on submit) + `defineWidget` accepts `paramsSchema`; 10 new vitest cases. | _this PR_ | Lights up **Tier-1 "Configure"** — a regular teacher can now pick `thermo-piston` / `number-line` from a gallery, fill a form generated from the kind's `params.schema.json`, watch a live sandboxed preview re-render on every keystroke, and attach the result to a subpart. Gallery filters hide framework-internal kinds and the admin-only `custom-html`. Preview passes empty variables for now; `{{var}}` substitution in preview is a follow-up. |
