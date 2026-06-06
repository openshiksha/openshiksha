# 2026-06-06 — IW-5 · Teacher widget gallery in CreateQuestionPage

## Summary

Lights up **Tier-1 "Configure"** of the Interactive Widgets Framework —
the teacher picks a registered widget from a gallery, fills in a form
auto-generated from the kind's `params.schema.json`, watches a live
preview re-render on every change, and the chosen `{kind, config}`
gets attached to the subpart on submit.

With this PR, *every* widget shipped on the framework
(`thermo-piston`, `number-line`) is reachable by a regular teacher
through the UI — no SQL, no Django admin, no IW-3b migration command.

## Classification

**New.** Authoring UX that didn't exist before this PR; legacy had no
analogue.

## What changed

- **`frontend_modern/src/widgets/_sdk/defineWidget.ts`** — `WidgetSpec`
  gains an optional `paramsSchema` field, and `WidgetModule` carries it
  through. Adding the schema travels-with-the-module gives the gallery
  *and* the eventual server-side per-kind validator one source of truth.
- **All shipped widgets** (`thermo-piston`, `number-line`,
  `custom-html`) import their sibling `params.schema.json` and pass it
  to `defineWidget`. The IW-8 scaffolder template was updated to do the
  same so future widgets are wired up by default.
- **`src/features/teacher/WidgetGalleryPanel.tsx`** (new):
  - **Gallery grid** lists every teacher-visible widget kind. Filters:
    - kinds prefixed `_` (framework-internal) are hidden
    - `custom-html` is hidden (admin-only escape hatch; future admin UI
      can flip this filter)
    - answer-producing kinds carry a small "answer" badge
  - **Configure view** auto-renders a form from the schema:
    - `number` → typed input that coerces back to `Number`
    - `string` → text input
    - `boolean` → checkbox
    - Required fields show a red asterisk
    - Defaults pre-fill on entry
    - Deprecated fields are silently hidden
    - Unknown / schema-less widgets fall back to a JSON textarea
      escape hatch with a banner
  - **Live preview** renders the widget inside the same sandboxed
    `<InteractiveWidget>` host every other surface uses; updates on
    every config change.
  - **Apply / Cancel** callbacks surface `{kind, config}` to the parent.
- **`src/features/teacher/CreateQuestionPage.tsx`**:
  - `SubpartDraft` gains `widget_kind` + `widget_config`. Loading an
    existing question and the LLM-draft "Use this" both round-trip the
    new fields.
  - New `WidgetPickerSection` block above the optional-image-URL row.
    Shows "+ Add interactive widget" when none is attached; when one is
    attached, summarises it (kind + field count) with Edit / Remove
    buttons. Opening either swaps the section for the
    `WidgetGalleryPanel` until Apply / Cancel.
  - `handleSubmit` includes `widget_kind` + `widget_config` in the
    write payload only when the kind is non-empty.
- **`src/types/index.ts`** — `QuestionSubpartWrite` gets the new fields
  documented (already on the read-side `Subpart` from IW-7).

## Test plan

- `WidgetGalleryPanel.test.tsx` (10 new vitest cases): gallery
  filtering (`_hello` hidden, `custom-html` hidden), answer-producing
  badge present, Cancel callback, gallery → configure transition,
  every schema property gets a labelled field (id `wgf-<name>`),
  preselecting via `initialKind` lands directly in configure mode and
  prefills the form, `Use this widget` surfaces `{kind, config}` to
  `onApply`, numeric inputs coerce back to `Number` not string.
- Full frontend suite — **160 passed** (was 150). Type-check / lint /
  build all clean.

## What's deliberately out of scope here

- **Schema validation in the UI.** The form coerces types but doesn't
  enforce `required` / `minimum` / `maximum` past displaying the red
  asterisk. The backend's writable serializer already accepts whatever
  shape; per-kind JSON Schema validation server-side is the IW-3
  follow-up that will eventually reject malformed configs at write time.
- **`{{var}}` substitution in the preview.** The gallery's preview
  passes `variables = {}` because it doesn't yet know what tokens the
  question will sample. Widgets that read `ctx.variables` (e.g.
  `thermo-piston`'s "your question values" hint) just show their
  fallback in the preview; substitution kicks in for real at student
  render time.
- **Admin gate for `custom-html`.** Still a `meta.title` affordance +
  the gallery filter; turning it into a real permission check needs
  the school-admin UI to land first.

## Next

- *(Follow-up)* `/widgets/dev` playground — the IW-8 backlog item the
  scaffolder PR deferred.
- *(Follow-up)* `migrate_legacy_interactive_html` management command —
  shifts any remaining legacy rows onto `widget_kind='custom-html'` so
  the `interactive_html` column can be dropped in a future PR.
- **IW-6** — library expansion (`function-plotter`, `fraction-bar`).
- **IW-9 full / IW-10** — Widget Studio runtime + UI (Tier-2 visual
  builder).
