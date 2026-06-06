# Anatomy of an Interactive Widget

> This is the **canonical contributor reference** for the Tier-3 SDK of
> the [Interactive Widgets Framework](../initiatives/interactive-widgets-framework.md).
> Worked examples drawn from the two widgets shipping on `modernization`
> today: [`_hello`](../../frontend_modern/src/widgets/_hello/index.ts)
> and [`thermo-piston`](../../frontend_modern/src/widgets/thermo-piston/index.ts).

A widget kind is **one folder under `frontend_modern/src/widgets/<kind>/`**
plus **one line in `registry.ts`**. The compounding goal of the
initiative is that adding a new widget never costs more than that, so
the framework's surface area stays tiny no matter how many widgets ship.

## Quick start

```bash
cd frontend_modern
npm run widget:new my-widget
```

That single command:

1. Creates `src/widgets/my-widget/{index.ts, params.schema.json, README.md}`
   from a tiny stub.
2. Patches `src/widgets/registry.ts` (import + entry) at the
   `widget:new` anchor comments.
3. Prints the one remaining manual step (the server-side
   `KNOWN_WIDGET_KINDS` mirror).

Then iterate on `index.ts` until your widget does what you want. Run
`npm run dev` and visit `/design`'s "Interactive Widgets" section to
see it render in the sandbox.

## The folder layout

```
src/widgets/<kind>/
├── index.ts            # default-exports defineWidget({ kind, version, meta, render })
├── params.schema.json  # JSON Schema for the per-question config the teacher fills in
└── README.md           # what the widget does + delta from any legacy reference
```

Folders starting with `_` (e.g. `_hello`) are framework-internal —
the teacher gallery filters them out. User-visible widgets use plain
kind names like `thermo-piston`, `number-line`, `function-plotter`.

## `defineWidget({ ... })`

The factory contributors call from `index.ts`. Its TypeScript shape
(`WidgetSpec`) is the contract:

```ts
defineWidget({
  kind: 'thermo-piston',   // matches the folder name + registry key
  version: 1,              // bump on a breaking config or behaviour change
  meta: {
    title: 'Thermodynamics — piston & First Law',
    description: 'Drag the heat slider and pump the piston to feel ΔU = ΔQ − ΔW.',
    answerProducing: false, // true if you ever call ctx.reportValue(...)
  },
  render: (ctx) => {
    // render runs INSIDE the sandboxed iframe — see "Render constraints" below.
    const el = document.createElement('p');
    el.textContent = 'Hello from ' + ctx.config.title;
    ctx.mount.appendChild(el);
  },
});
```

The factory validates the spec at app-bundle time and throws on
malformed input — empty `kind`, non-integer `version`, missing
`meta.title`, etc. Catch your mistakes before they reach the registry.

## The `ctx` argument

Everything `render` can do — read its config, sample variables, report
an answer, request a resize — arrives on a single `WidgetContext`
object:

```ts
interface WidgetContext {
  mount: HTMLElement;                                  // your DOM root, already in the sandbox
  config: Record<string, unknown>;                     // per-student-resolved widget_config
  variables: Record<string, number | string | boolean>; // sampled variables for this student
  imageBase: string;                                   // absolute URL prefix for relative assets
  reportValue: (value: unknown) => void;               // answer-producing widgets only
  requestResize: () => void;                           // explicit resize signal (rarely needed)
}
```

`config` is what `params.schema.json` describes: the teacher fills in
those fields when authoring a question, and the croupier substitutes
`{{var}}` tokens before the host bakes it into the sandbox.

`variables` are the per-student random values (`{k: 80, j: 30}`,
etc.) — same values the question text already shows. Use them to keep
the widget's view of the world correlated with the question copy.

`reportValue` is for **answer-producing** widgets (IW-4). Calling it
posts a typed `value` message that the host bridges into the
submission form. **Don't call it from explanatory widgets** — the
student types their answer separately.

`requestResize` forces an immediate `resize` post. The runtime
already auto-resizes via `ResizeObserver` whenever the body grows or
shrinks, so this is only needed for edge cases where the observer
might miss (most widgets never call it).

## Render constraints (read these — they trip everyone up once)

The `render` function runs **inside the sandboxed iframe**, not the
app bundle. The runtime serialises it via
`Function.prototype.toString()` and inlines the resulting source string
into the iframe srcdoc. That has three consequences:

1. **No captured closures.** Anything `render` references must arrive
   on `ctx` or live on `globalThis`. A captured variable from the
   surrounding module is *not* in scope at runtime.
2. **No app-bundle imports.** The sandbox has zero app code by
   design — that is the security boundary. React, lodash, your shared
   utility module, your design tokens — none of them are reachable
   from inside `render`.
3. **Self-contained function literal.** Write `render` as a single
   arrow function or `function` expression so it stringifies cleanly.
   Inline whatever helpers it needs.

The framework will not stop you from breaking these rules — it can't
inspect the function body — but the widget will silently fail at
runtime (a captured `useState` reference becomes a `ReferenceError`
inside the sandbox). Stick to vanilla DOM + SVG and you'll be fine.

## The wire protocol (in case you need it)

Most widgets never touch the protocol directly — `ctx.reportValue` /
`ctx.requestResize` are the only paths a render function uses. The
full surface is in
[`frontend_modern/src/widgets/_sdk/protocol.ts`](../../frontend_modern/src/widgets/_sdk/protocol.ts):

| Direction | Type | Purpose |
|---|---|---|
| Host → widget | `init` | One-shot config + variables + imageBase payload. Baked into the boot script. |
| Widget → host | `ready` | Sent at boot. Lets the host bridge know the runtime is alive. |
| Widget → host | `resize` | Auto-emitted by `ResizeObserver` whenever the body's size changes. |
| Widget → host | `value` | Answer payload. Triggered by `ctx.reportValue(v)`. |
| Widget → host | `error` | Exception summary. Caught by the runtime; rendered as a small notice under the iframe. |

Every message carries the protocol version. A widget written against
v1 will refuse to talk to a future v2 host (and vice versa) rather
than silently misbehaving.

## Security model (one paragraph)

The iframe uses `sandbox="allow-scripts"` and deliberately not
`allow-same-origin`. That combination would let the authored script
read the app's cookies/storage/DOM and defeats the whole point. The
widget HTML is delivered only via `srcDoc` (an opaque-origin document)
— it is never injected into the app DOM. Identity of messages coming
back from the iframe is enforced via `event.source === iframe.contentWindow`
(not `event.origin`, which is the literal string `"null"` for an
opaque-origin sandboxed document). All of this lives in
`_sdk/host.ts`; widget authors never need to think about it as long
as they don't sneak in an `allow-same-origin` somewhere.

## Server-side mirror

The DB validates `widget_kind` against
[`backend/openshiksha/apps/core/widgets.py`](../../backend/openshiksha/apps/core/widgets.py)'s
`KNOWN_WIDGET_KINDS` set. The two registries are kept in sync by
hand: add your kind to both. The scaffolder's CLI output reminds you
of this every run.

## Worked examples

- **`_hello`** — the simplest possible widget. Vanilla DOM. Six lines
  of render body. The IW-1 loop proof.
  [`src/widgets/_hello/index.ts`](../../frontend_modern/src/widgets/_hello/index.ts)
- **`thermo-piston`** — a real explanatory widget. SVG cylinder +
  gas + piston, a slider drives ΔQ, buttons drive ΔW, kinetic-theory
  particles vibrate with internal energy `ΔU = ΔQ − ΔW`. ~3 KB of
  vanilla DOM replaces ~280 KB of legacy jQuery / Bootstrap.
  [`src/widgets/thermo-piston/index.ts`](../../frontend_modern/src/widgets/thermo-piston/index.ts)

When in doubt, copy the closest example and trim.
