# `custom-html` widget — the escape hatch (admin only)

> The piece of the [Interactive Widgets Framework](../../../../docs/initiatives/interactive-widgets-framework.md)
> that absorbs every remaining authoring path. With this kind in the
> registry, the legacy `QuestionSubpart.interactive_html` raw-HTML
> field can be marked deprecated — every widget on the platform now
> flows through the same sandboxed `<InteractiveWidget>` host.

## What it does

Renders an arbitrary HTML string inside the sandboxed iframe. Inline
and `src`-style `<script>` tags are re-executed in document order
after the HTML is inserted (a plain `innerHTML` assignment does *not*
execute scripts — browsers inert them on purpose).

This widget is **explanatory only**. It never calls `reportValue`; if
the authored HTML needs to produce an answer, the student types it
into the normal answer field below the widget, as in the legacy flow.

## When to use this

**Almost never.** In priority order, prefer:

1. A first-party widget (`thermo-piston`, future `number-line`,
   `function-plotter`, `fraction-bar`, …) — the gallery + JSON Schema
   form gives every teacher a no-code path.
2. A Tier-2 Studio scene (`studio-scene`, IW-9/10) — composes a widget
   from primitives without code.
3. A new Tier-3 widget kind — one file under `src/widgets/<kind>/` via
   `npm run widget:new <kind>`. Reviewable, typed, reusable.

`custom-html` exists for the residual cases the above three can't
express — usually one-off bespoke content with embedded jQuery, SVG,
or a vendor library the platform doesn't ship. It is **gated to school
admins** in the teacher gallery (IW-5 enforces this); regular teachers
cannot attach raw HTML to a question.

## Config

See [`params.schema.json`](./params.schema.json). One required field:

- `html` *(string, required)* — the HTML body the widget renders.
  `{{var}}` tokens are substituted server-side by the croupier
  (IW-3b) just like any other widget config string.

## Security

Identical to every other widget: `sandbox="allow-scripts"` without
`allow-same-origin`, opaque-origin srcdoc, identity enforced by
`event.source` (see [`docs/widgets/anatomy.md`](../../../../docs/widgets/anatomy.md#security-model-one-paragraph)).
The authored scripts cannot reach the app's cookies, storage, or DOM.
That said — **it is still your code shipping to students**, which is
why this kind is admin-gated.

## How it relates to the legacy `interactive_html` field

`QuestionSubpart.interactive_html` (M7-11) was the *raw* escape hatch:
authored HTML stored on the row, rendered via `buildLegacySrcDoc`
which inlined jQuery + jQuery-UI + Bootstrap 3 glyphicons by default.

`custom-html` is the **structured replacement**: the same HTML lives
in `widget_config.html` and renders via `buildHostSrcDoc` + the SDK
runtime. No vendor head is auto-injected — if the HTML needs jQuery,
the author includes `<script src="…/jquery.min.js"></script>` in the
HTML itself; the script re-execution loop loads it.

When the eventual one-shot migration command lands
(`migrate_legacy_interactive_html`, follow-up), it will stamp each
legacy row with `widget_kind='custom-html'` + `widget_config={html:
<row.interactive_html>}` and clear `interactive_html`. The deprecation
note on the field already calls this out as of IW-7.
