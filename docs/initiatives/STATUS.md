# Initiatives - Status Board

> The live priority order for long-horizon work. A routine with no higher-priority
> task advances the **top active initiative** here. See [`README.md`](README.md)
> for how. Keep this file short - one row per initiative.

**Last updated:** 2026-06-07 - **Legacy parity and the current mobile shell
scope are closed.** Interactive Widgets IW-1 through IW-8 are shipped and
valuable: developer-authored widgets are easy to build, registry widgets are
available in the question creator, and all render through the shared sandbox.
IW-9/IW-10/IW-11 are intentionally deferred until Widget Studio has a clearer
teacher-facing product pull.

| Priority | Initiative | Status | Headline progress | Next increment |
|:--:|---|---|---|---|
| - | [Interactive Widgets Framework](interactive-widgets-framework.md) | Paused | Tier 1 **Configure** is usable (`WidgetGalleryPanel` + registry schemas). Tier 3 **Code** is usable (`defineWidget`, `npm run widget:new`, `npm run widget:dev -- <kind>`, `/widgets/dev`, docs). First-party library currently includes `_hello`, `thermo-piston`, `number-line`, `function-plotter`, `fraction-bar`, plus admin-only `custom-html`; all render through the same sandboxed iframe and answer-producing widgets report through the shared protocol. | Defer **IW-9 - IW-11** until product discovery proves Widget Studio is more valuable than more first-party/developer-authored widgets. |
| - | [V2 "Chalk & Unlock" design overhaul](2026-design-system-v2.md) | Done | M1-M7 are closed for the current scope. Mobile shell now has role-aware bottom tabs, account drawer, safe-area/dynamic-viewport padding, large touch targets, responsive surface audit, and focused a11y baseline. Legacy parity gaps are closed or explicitly skipped. Only optional activation remains: run the [seed-visual-baselines](../../.github/workflows/seed-visual-baselines.yaml) workflow once for M6-03 baselines. | - |
| - | [Cabinet Data Fidelity](cabinet-data-fidelity.md) | Done | Closing batch shipped (M7-08, M7-06, M7-03a/b, fidelity-audit guard) + proper taxonomy names baked into the importer. `audit_cabinet_fidelity --strict` is **green on the real 646-question corpus**. M7-11 sandbox primitive shipped and now seeds the new **Interactive Widgets Framework** initiative. | - |

## Legend

- **Active** - being advanced now; pull its top increment.
- **Paused** - intentionally on hold (reason in the doc).
- **Proposed** - written up but not yet started.
- **Done** - North Star reached; keep for history.

## Backlog of future initiatives (proposed, not yet scoped)

These are candidate long-horizon goals. Promote one to its own doc when it
becomes the right next bet.

- **Mobile shell** - bottom tab bar shipped 2026-06-04 (#195 / `M5-01`).
  Remaining work for a proper proposal: route-level mobile layouts, PWA
  install, offline-tolerant question viewing.
- **AI tutor surface** - student-facing conversational help over the existing
  hint + explanation backends. A branch (`ai/2026-06-04-ai-tutor-chat`,
  commit `1e3c50f9`) has a Socratic chat coded but diverged ~5 000 lines from
  `modernization`. Promotion = rebase, harden, formalise.
- **Accessibility pass** - WCAG 2.1 AA across the migrated V2 surfaces. A
  focused baseline pass landed 2026-06-04 (M6-01 #202) - skip link, dialog
  semantics, image alts. Promote to its own initiative when ready for a
  full audit (keyboard walkthrough, screen-reader spot-check, axe-core CI).
- **Performance budget** - route-level code-splitting, image/font
  optimisation. The build warns `dist/assets/index-*.js 770 kB`; one bundle =
  slow first paint on K-12 mobile networks.
