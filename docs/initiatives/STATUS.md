# Initiatives - Status Board

> The live priority order for long-horizon work. A routine with no higher-priority
> task advances the **top active initiative** here. See [`README.md`](README.md)
> for how. Keep this file short - one row per initiative.

**Last updated:** 2026-06-07 (closeout) - **Performance Budget done.** Shipped
PERF-01..04 + PERF-06 in one batch ([#251](https://github.com/openshiksha/openshiksha/pull/251),
[#252](https://github.com/openshiksha/openshiksha/pull/252),
[#253](https://github.com/openshiksha/openshiksha/pull/253),
[#254](https://github.com/openshiksha/openshiksha/pull/254),
[#255](https://github.com/openshiksha/openshiksha/pull/255)). Entry chunk
**855 → 131 kB / 247 → 41 kB gzip** (84% gzip drop), KaTeX off the first-paint
critical path, CI guard at 160 kB defends the cut. PERF-05 (font self-hosting)
deferred — real-device measurement showed fonts aren't the long pole.
**Teacher Workspace** remains the active top initiative.

| Priority | Initiative | Status | Headline progress | Next increment |
|:--:|---|---|---|---|
| 1 | [Teacher Workspace](teacher-workspace.md) | Active | Promoted 2026-06-07 (user-directed). [#248](https://github.com/openshiksha/openshiksha/pull/248) fixed the worst breakage (join code, read-only student preview, decluttered dashboard). TW-1 in flight: Assign deep-links (`?problemSet=`/`?room=`) preselect the set/room, and a "preview the actual questions as a student" link lands before publish. | **TW-1** (shipping), then TW-3/TW-4/TW-5 polish. **TW-2** (editable preview) is blocked on [Authoring Integrity](authoring-integrity-versioning.md) Phase 1 snapshots. |
| - | [Performance Budget](performance-budget.md) | Done | Closed 2026-06-07. PERF-01..04 + PERF-06 shipped in one batch ([#251](https://github.com/openshiksha/openshiksha/pull/251)–[#255](https://github.com/openshiksha/openshiksha/pull/255)); entry chunk **855 → 131 kB / 247 → 41 kB gzip** (84% gzip drop); vendor split, route-level `React.lazy`, lazy KaTeX behind `<RichContent>`, CI budget guard at 160 kB. Production also drops `ReactQueryDevtools` via `import.meta.env.DEV` guard. | - |
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
- **[Authoring Integrity & Versioning](authoring-integrity-versioning.md)** -
  ⚪ Proposed (2026-06-07). Editing a problem set / question today retroactively
  changes already-assigned and already-graded work, because `grade_submission`
  reads the **live** set + correct answers. Phase 1 (per-assignment content
  snapshot) removes that silent-corruption risk and unblocks an **editable**
  teacher preview; later phases add versioning + a guarded re-sync. Motivated by
  the editable-preview ask on [#248](https://github.com/openshiksha/openshiksha/pull/248).
- _(Promoted 2026-06-07 → [Performance Budget](performance-budget.md), now the
  active top initiative.)_
