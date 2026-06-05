# Initiatives — Status Board

> The live priority order for long-horizon work. A routine with no higher-priority
> task advances the **top active initiative** here. See [`README.md`](README.md)
> for how. Keep this file short — one row per initiative.

**Last updated:** 2026-06-04 — **Interactive Widgets Framework promoted to #1
active.** V2 "Chalk & Unlock" backlog is `[x]` end-to-end except for explicitly
deferred non-goals (full a11y audit, axe-core CI gating, authenticated-surface
visual snapshots) — promoted to ✅ closing so routines advance the next
top priority.

| Priority | Initiative | Status | Headline progress | Next increment |
|:--:|---|---|---|---|
| 1 | [Interactive Widgets Framework](interactive-widgets-framework.md) | 🟢 Active | Just promoted (2026-06-04). M7-11 sandbox seed already shipped (#132 / [`InteractiveWidget.tsx`](../../frontend_modern/src/shared/ui/InteractiveWidget.tsx)) so the runtime trigger is met. Full IW-1 → IW-8 backlog written, DX-first principles encoded, V2-brand inside the sandbox required. Goal: a new widget kind is one `defineWidget(...)` file + a JSON Schema, scaffolded by `npm run widget:new <kind>`, hot-reloading in a dev playground, ready in < 30 min for a first-time author. | **IW-1 — Runtime + SDK skeleton.** Convert the M7-11 host into a reusable runtime (typed `host.ts`/`runtime.ts`/`protocol.ts`); add an empty `registry.ts`; ship a "hello-widget" to prove the loop end-to-end; rewire `<InteractiveWidget>` through `_sdk/host.ts` so the legacy thermo path stays green. Full DoD in [the initiative doc](interactive-widgets-framework.md#d-backlog--iw-1--iw-8-each--one-reviewable-pr--batch-item). |
| — | [V2 "Chalk & Unlock" design overhaul](2026-design-system-v2.md) | ✅ Closing | M1–M7 all `[x]` or `[~]` with documented activation steps. Final batch shipped 2026-06-04 (#188–#207) — M4 closed; M5-01/02, M6-01/02/03 (scaffold + workflow), M7-01/02/03/04/05 all shipped. Only one-click activations remain: run the [seed-visual-baselines](../../.github/workflows/seed-visual-baselines.yaml) workflow once for M6-03 baselines; set `OPENSHIKSHA_ADMIN_EMAILS` env in prod for concierge enquiry email (#205). | — (initiative closing) |
| — | [Cabinet Data Fidelity](cabinet-data-fidelity.md) | ✅ Done | Closing batch shipped (M7-08, M7-06, M7-03a/b, fidelity-audit guard) + proper taxonomy names baked into the importer. `audit_cabinet_fidelity --strict` is **green on the real 646-question corpus**. M7-11 sandbox primitive shipped and now seeds the new **Interactive Widgets Framework** initiative. | — |

## Legend

- 🟢 **Active** — being advanced now; pull its top increment.
- 🟡 **Paused** — intentionally on hold (reason in the doc).
- ⚪ **Proposed** — written up but not yet started.
- ✅ **Done** — North Star reached; keep for history.

## Backlog of future initiatives (proposed, not yet scoped)

These are candidate long-horizon goals. Promote one to its own doc when it
becomes the right next bet.

- **Mobile shell** — bottom tab bar shipped 2026-06-04 (#195 / `M5-01`).
  Remaining work for a proper proposal: route-level mobile layouts, PWA
  install, offline-tolerant question viewing.
- **AI tutor surface** — student-facing conversational help over the existing
  hint + explanation backends. A branch (`ai/2026-06-04-ai-tutor-chat`,
  commit `1e3c50f9`) has a Socratic chat coded but diverged ~5 000 lines from
  `modernization`. Promotion = rebase, harden, formalise.
- **Accessibility pass** — WCAG 2.1 AA across the migrated V2 surfaces. A
  focused baseline pass landed 2026-06-04 (M6-01 #202) — skip link, dialog
  semantics, image alts. Promote to its own initiative when ready for a
  full audit (keyboard walkthrough, screen-reader spot-check, axe-core CI).
- **Performance budget** — route-level code-splitting, image/font
  optimisation. The build warns `dist/assets/index-*.js 770 kB`; one bundle =
  slow first paint on K-12 mobile networks.
