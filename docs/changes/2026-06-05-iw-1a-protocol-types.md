# 2026-06-05 — IW-1a · Protocol types for the Widgets Framework

## Summary

Lands the **wire contract** between the parent host and the sandboxed widget
runtime. Pure TypeScript — zero runtime impact on the app today. This is the
foundation IW-1b (host module) and IW-1c (runtime + hello-widget) will both
import.

## Classification

**New.** Tier-3 SDK contract; no legacy analogue.

## What changed

- **`frontend_modern/src/widgets/_sdk/protocol.ts`** (new) — the wire format:
  - `WIDGET_PROTOCOL_VERSION = 1` — both sides pin and refuse mismatches
  - `HostMessage = InitMessage` (host → widget)
  - `WidgetMessage = ReadyMessage | ResizeMessage | ValueMessage | ErrorMessage` (widget → host)
  - Narrow type guards (`isInitMessage`, `isReadyMessage`, `isResizeMessage`,
    `isValueMessage`, `isErrorMessage`, `isWidgetMessage`) that check the
    discriminant + protocol version + the one structural invariant each
    payload requires
- **`frontend_modern/src/widgets/_sdk/protocol.test.ts`** (new) — 10 cases
  covering positive matches, version mismatches, null / primitive garbage, and
  cross-direction rejection (host-bound messages don't satisfy widget-bound
  guards).

## Security note

`event.origin` is `"null"` for an `allow-scripts` sandbox without
`allow-same-origin`, so identity in the host bridge will be enforced via
`event.source === iframe.contentWindow`, not the origin string. The protocol
types deliberately do not include origin fields — that check is the host's
job, not the wire format's.

## Why one tiny file as its own PR

Plan-1 calls for IW-1 to land in three stacked PRs (types → host → runtime).
This PR is the bottom of that stack: pure types, no runtime change, no
behavioural risk. The host module (IW-1b) and runtime (IW-1c) each consume
this without ambiguity, and the small surface area is genuinely useful to
review in isolation.

## Tests

- `npm test` (vitest, `protocol.test.ts`) — 10 passed
- `npm run type-check` — clean
- `npm run lint` — clean
- `npm run build` — clean

## Next

- **IW-1b** (next PR) — `host.ts` module + rewire `InteractiveWidget.tsx` to
  delegate srcdoc + bridge construction through the SDK.
- **IW-1c** (after IW-1b) — runtime + hello-widget + `/design` showcase.
