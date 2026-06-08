# Initiatives - Status Board

> The live priority order for long-horizon work. A routine with no higher-priority
> task advances the **top active initiative** here. See [`README.md`](README.md)
> for how. Keep this file short - one row per initiative.

**Last updated:** 2026-06-07 — **Teacher Workspace mostly closed.** All
unblocked TW increments shipped today across **#250, #261–#266**
(TW-1, TW-5, TW-4, TW-3a, TW-3b, TW-6, TW-7). The previously-planned **TW-T**
Playwright continuity smoke was **dropped from the backlog** — the seams it
covers are already exercised by Vitest + pytest, and a backend-dependent
Playwright project is disproportionate infra for one smoke test. **TW-2**
(editable preview) is the only open increment and remains blocked on
[Authoring Integrity](authoring-integrity-versioning.md) Phase 1 snapshots.
Earlier today: **Performance Budget done** (PERF-01..04 + PERF-06
in [#251](https://github.com/openshiksha/openshiksha/pull/251)–[#255](https://github.com/openshiksha/openshiksha/pull/255);
[#256](https://github.com/openshiksha/openshiksha/pull/256) for the DOMPurify
barrel-export leak). Entry chunk **855 → 93 kB / 247 → 29 kB gzip**, CI guard
at 160 kB defends the cut.

| Priority | Initiative | Status | Headline progress | Next increment |
|:--:|---|---|---|---|
| 1 | [Teacher Workspace](teacher-workspace.md) | Paused | All unblocked increments shipped 2026-06-07: TW-1 ([#250](https://github.com/openshiksha/openshiksha/pull/250)), TW-5 ([#261](https://github.com/openshiksha/openshiksha/pull/261)), TW-4 ([#262](https://github.com/openshiksha/openshiksha/pull/262)), TW-3a ([#263](https://github.com/openshiksha/openshiksha/pull/263)), TW-3b ([#264](https://github.com/openshiksha/openshiksha/pull/264)), TW-6 ([#265](https://github.com/openshiksha/openshiksha/pull/265)), TW-7 ([#266](https://github.com/openshiksha/openshiksha/pull/266)). TW-T smoke test dropped (see initiative doc). | **TW-2** (editable preview) — blocked on [Authoring Integrity](authoring-integrity-versioning.md) Phase 1 snapshots. Unpause this initiative when AIV-1..3 lands. |
| - | [Performance Budget](performance-budget.md) | Done | Closed 2026-06-07. PERF-01..04 + PERF-06 shipped in one batch ([#251](https://github.com/openshiksha/openshiksha/pull/251)–[#255](https://github.com/openshiksha/openshiksha/pull/255)); follow-up ([#256](https://github.com/openshiksha/openshiksha/pull/256)) dropped `ReactQueryDevtools` in prod, added a measurement harness, and fixed a `@/shared/ui` barrel-export leak that was dragging DOMPurify into the entry chunk. Entry chunk **855 → 93 kB / 247 → 29 kB gzip** (88% gzip drop); vendor split, route-level `React.lazy`, lazy KaTeX behind `<RichContent>`, CI budget guard at 160 kB. Measured `/login` FCP under Slow 4G + 4× CPU: 4.4 s. | - |
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
