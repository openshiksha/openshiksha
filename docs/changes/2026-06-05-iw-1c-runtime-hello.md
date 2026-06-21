# 2026-06-05 — IW-1c · Runtime + `_hello` widget + registry barrel + `/design` showcase

## Summary

Closes the IW-1 stack. The Widgets Framework now renders end-to-end: a
contributor calls `defineWidget()`, registers the kind in `registry.ts`,
and the host's `buildHostSrcDoc` wraps the widget's render function with
the runtime boot (`reportValue`, `requestResize`, auto-resize) and inlines
it into the sandbox srcdoc. Unknown kinds get a typed `error` fallback
instead of silently no-op'ing.

The `_hello` reference widget proves the loop in the `/design` page.

## Classification

**New** (SDK + reference widget) + small **Improve** (`InteractiveWidget.tsx`
extended to accept `kind`/`config` mode while keeping the legacy `html`
path).

## What changed

- **`frontend_modern/src/widgets/_sdk/defineWidget.ts`** (new) — the
  Tier-3 factory. Returns a `WidgetModule` with a stringified
  `renderSource`. Validates `kind` / `version` / `render` / `meta.title`
  loudly so a malformed widget never silently registers.
- **`frontend_modern/src/widgets/_sdk/runtime.ts`** (new) — the boot
  script that runs **inside the sandbox**. Wraps the widget's
  `renderSource` with the SDK hooks, sets up a `ResizeObserver` →
  typed `resize`, catches exceptions → typed `error`, escapes
  `</script>` in both the init payload and the render source.
- **`frontend_modern/src/widgets/registry.ts`** (new) — single source of
  truth for kinds the frontend knows about. Includes the `widget:new
  inserts here` anchor for the IW-8 scaffolder.
- **`frontend_modern/src/widgets/_hello/index.ts`** (new) — the loop-proof
  widget. Vanilla DOM (React-in-sandbox lands with IW-2's
  `thermo-piston`).
- **`frontend_modern/src/widgets/_sdk/host.ts`** — `buildHostSrcDoc` now
  resolves `kind` against the registry and bakes the runtime boot for it;
  unknown kinds get a typed `error` boot. Brand tokens + protocol wire
  unchanged from IW-1b.
- **`frontend_modern/src/shared/ui/InteractiveWidget.tsx`** — adds a
  `kind` / `config` / `variables` / `imageBase` mode (used when `kind`
  is present); the legacy `html` mode stays byte-identical. Lifts the
  iframe to a V2-token shell (`#FBF7EE` warm paper card, `#FF6F00`
  brand-tinted top border) — the runtime now feels on-brand from day one.
  Renders the widget's typed `error` payload as a small inline notice
  beneath the iframe when one fires.
- **`frontend_modern/src/features/design/DesignSystemPage.tsx`** —
  adds the "Interactive Widgets · IW-1c · Runtime preview" section that
  mounts `_hello` through the new framework path beside the existing
  legacy showcase.
- **`frontend_modern/src/widgets/README.md`** (new) — the file a
  newcomer opens first: layout, "how to add a new widget kind",
  render-function constraints, pointers into the SDK + initiative doc.
- **Tests** — `defineWidget.test.ts` (6 cases), `registry.test.ts`
  (4 cases), `host.test.ts` (+2 cases for registry-resolved vs.
  unknown-kind boot). Total **125/125** vitest pass.

## Security model

Unchanged from IW-1b. The runtime boot adds the same `<` escape on the
render source so an authored `</script>` cannot break out of the inline
script tag, on top of the IW-1b escape on the init payload. The sandbox
attrs (`sandbox="allow-scripts"`, no `allow-same-origin`) still live on
the `<iframe>` element. The bridge still requires
`event.source === iframe.contentWindow` before any handler fires.

## Why vanilla render for `_hello`

`_hello`'s render is vanilla DOM (`document.createElement('p')`) because
IW-1c's runtime does not bootstrap React inside the sandbox. IW-2
introduces React-in-sandbox alongside the `thermo-piston` widget; once
that lands, JSX-driven widgets work without an SDK change. Vanilla DOM is
enough to prove the loop and keep the runtime tiny.

## Tests

- `npm test` — 125 passed (10 protocol + 16 host + 6 defineWidget + 4
  registry + 4 legacy InteractiveWidget + 85 other)
- `npm run type-check` — clean
- `npm run lint` — clean
- `npm run build` — clean; `_hello`'s render source verified inlined in
  the bundle output

## Next

- **IW-2** — `thermo-piston` widget: React-in-sandbox + the legacy
  thermo question data flip onto `widget_kind="thermo-piston"` via the
  already-shipped migration command (#212).
- **IW-8-early** — `npm run widget:new <kind>` scaffolder using the
  `widget:new inserts here` anchor + `docs/widgets/anatomy.md`.
