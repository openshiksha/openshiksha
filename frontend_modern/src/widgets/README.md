# `src/widgets/` — Interactive Widgets Framework

This folder is the **Tier-3 (contributor) authoring surface** for the
[Interactive Widgets Framework](../../../../docs/initiatives/interactive-widgets-framework.md).
Every interactive widget the platform ships — explanatory (e.g. the legacy
Class-11 thermo piston) or answer-producing (e.g. `number-line`,
`function-plotter`) — lives here as **one folder per kind**.

## Layout

```
src/widgets/
├── _sdk/                # Framework code (protocol, host, runtime, defineWidget)
│   ├── protocol.ts      # Wire types between host ↔ sandboxed runtime
│   ├── host.ts          # srcdoc builders + message bridge (used by InteractiveWidget)
│   ├── runtime.ts       # Boot script that runs inside the sandbox
│   └── defineWidget.ts  # Factory contributors call from their widget module
├── _hello/              # Reference / loop-proof widget (IW-1c)
│   └── index.ts
└── registry.ts          # The single source of truth for which kinds exist
```

Folders prefixed with `_` are framework-internal and never surface in the
teacher gallery (IW-5). User-visible widgets use plain kind names —
`thermo-piston`, `number-line`, `fraction-bar`, etc.

## Adding a new widget kind

A widget is **one file + one registry entry**. From inside this folder:

1. Create `src/widgets/<kind>/index.ts` (or `.tsx` once React-in-sandbox lands
   with IW-2) that default-exports a `defineWidget({...})` call.
2. Append `<kind>` to `widgetRegistry` in `registry.ts`.
3. Add the same key to `KNOWN_WIDGET_KINDS` in
   `backend/openshiksha/apps/core/widgets.py` so the writable serializer
   accepts it.

The scaffolder (`npm run widget:new <kind>`, IW-8) automates 1 + 2.

### Render-function constraints

Your `render` is **executed inside the sandboxed iframe**, not the app
bundle. It is serialised via `Function.prototype.toString()` at srcdoc-build
time and inlined into the boot script, so:

- **No captured closures** — anything you reference must arrive via the
  `ctx` parameter (`mount`, `config`, `variables`, `imageBase`,
  `reportValue`, `requestResize`).
- **No app-bundle imports** — the sandbox has zero app code by design.
- **Self-contained expression** — write `render` as a single function
  literal so it stringifies cleanly.

## Pointers

- The full architecture and design principles: [`docs/initiatives/interactive-widgets-framework.md`](../../../../docs/initiatives/interactive-widgets-framework.md)
- The host module: [`_sdk/host.ts`](./_sdk/host.ts)
- The wire protocol: [`_sdk/protocol.ts`](./_sdk/protocol.ts)
- The reference widget: [`_hello/index.ts`](./_hello/index.ts)
