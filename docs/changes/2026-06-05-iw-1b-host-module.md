# 2026-06-05 — IW-1b · Widgets Framework host module

## Summary

Factors the srcdoc construction and message bridge out of
`InteractiveWidget.tsx` and into a reusable `_sdk/host.ts` module.
**The legacy thermo path is byte-equivalent** — `buildLegacySrcDoc` returns
the exact string the previous inline implementation produced, so the M7-11
widget continues to render unchanged. The new framework path (`buildHostSrcDoc`)
is ready for IW-1c's runtime to drop into.

## Classification

**Improve** (refactor + extend). Plus a small **New** in the typed protocol
wire-up for the framework path.

## What changed

- **`frontend_modern/src/widgets/_sdk/host.ts`** (new):
  - `buildLegacySrcDoc(html)` — byte-equivalent legacy escape-hatch srcdoc
    with jQuery / jQuery-UI / Bootstrap 3 vendor head + `os-widget-height`
    resize script.
  - `buildHostSrcDoc({ kind, config, variables, imageBase })` — framework
    path; no vendor libs; React-only; bakes a JSON `init` payload (safely —
    every `<` escaped to `<` so embedded `</script>` cannot break out);
    emits typed `ready` + `resize` over the IW-1a protocol; uses brand
    tokens (`#FF6F00`, Fraunces, warm paper) inline so widgets read
    on-brand from day one.
  - `createHostBridge(getIframe, handlers)` — single source-guarded
    `window.addEventListener('message', ...)` that filters events by
    `event.source === iframe.contentWindow` *before* dispatching. Handlers:
    `onLegacyHeight` (the M7-11 shape) and `onReady` / `onResize` /
    `onValue` / `onError` (typed protocol). Returns a cleanup fn.
- **`frontend_modern/src/shared/ui/InteractiveWidget.tsx`** — now delegates
  srcdoc construction to `buildLegacySrcDoc` and bridge construction to
  `createHostBridge`. Public `InteractiveWidgetProps` (`html`,
  `fallbackText`, `minHeight`, `className`) **unchanged** so every existing
  consumer keeps working without a code change.
- **`frontend_modern/src/widgets/_sdk/host.test.ts`** (new) — 14 vitest
  cases:
  - legacy srcdoc: no `allow-same-origin` reference; jQuery vendor head
    preserved; `os-widget-height` shape preserved; authored HTML embedded
    verbatim
  - host srcdoc: no vendor libs; pins `WIDGET_PROTOCOL_VERSION`;
    `</script>` escape (XSS-safe init payload); emits `ready` + `resize`;
    brand tokens present
  - bridge: ignores messages from any source ≠ the bound iframe; delivers
    both legacy and typed messages from the right iframe; drops malformed
    payloads silently; cleanup detaches the listener

## Security model

The iframe attributes (`sandbox="allow-scripts"`, no `allow-same-origin`)
stay on the `<iframe>` element so React's type-system + the existing
`InteractiveWidget.test.tsx` regression catches any drift. The host module
never builds an iframe; it only builds *what goes into one*. Identity of
messages is enforced by `event.source` (an `allow-scripts` sandbox without
`allow-same-origin` has `event.origin === "null"`).

## Tests

- `npm test` — 113 passed (10 IW-1a protocol + 14 IW-1b host + 4 legacy
  InteractiveWidget + 85 other)
- `npm run type-check` — clean
- `npm run lint` — clean
- `npm run build` — clean

## Next

- **IW-1c** — runtime + `widgets/registry.ts` empty barrel + `_hello/`
  reference widget + `/design` showcase. `buildHostSrcDoc`'s init payload
  contract is finalised here, so IW-1c is a body swap (replace the stub
  render with a real registry lookup), not an API change.
