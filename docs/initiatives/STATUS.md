# Initiatives — Status Board

> The live priority order for long-horizon work. A routine with no higher-priority
> task advances the **top active initiative** here. See [`README.md`](README.md)
> for how. Keep this file short — one row per initiative.

**Last updated:** 2026-06-04 — **M4 closed** (every authenticated surface on V2). Same-day bonus: M6-02 (retire `primary`), M7-03 (Browse Grade filter), and M5-01 (mobile bottom tab bar) all shipped. See PRs #188–#195.

| Priority | Initiative | Status | Headline progress | Next increment |
|:--:|---|---|---|---|
| 1 | [V2 "Chalk & Unlock" design overhaul](2026-design-system-v2.md) | 🟢 Active | **M1, M2-01, M2-03, M3-01/02/04, M4 (all of it), M5-01, M6-02, M7-01/02/05 done.** Only `M2-02` (mobile nav polish), `M3-03` (public Enquire), `M4` design-polish, `M5-02` (responsive audit), `M6-01` (a11y audit), `M6-03` (visual-regression set), and remaining `M7-03` (Question Bank + assignment-list filter parity) / `M7-04` (legacy-feature-parity audit) remain. **The whole product wears one branded language; the legacy `primary` blue palette no longer exists in the repo.** | Pull the highest-value remaining unblocked item. Strongest candidates: **M2-02** (now that bottom tabs cover primary nav, the hamburger menu can shrink to a secondary tray), **M3-03** (Enquire — visible to prospective schools), **M7-03** (finish list-page filter parity on Question Bank + assignment lists), or **M6-01** (AA audit across the now-coherent V2 surfaces). |
| — | [Cabinet Data Fidelity](cabinet-data-fidelity.md) (M7-03/06/08) | ✅ Done | Closing batch shipped (M7-08, M7-06, M7-03a/b, fidelity-audit guard) + proper taxonomy names baked into the importer. `audit_cabinet_fidelity --strict` is **green on the real 646-question corpus** (0 wrong-widget, 0 token leaks, 0 placeholders, every id→1 Q). Residuals: image count 138 (<500, follow-up) and the additive **M7-11 interactive widget** (in progress). | — |

## Legend

- 🟢 **Active** — being advanced now; pull its top increment.
- 🟡 **Paused** — intentionally on hold (reason in the doc).
- ⚪ **Proposed** — written up but not yet started.
- ✅ **Done** — North Star reached; keep for history.

## Backlog of future initiatives (proposed, not yet scoped)

These are candidate long-horizon goals. Promote one to its own doc when it
becomes the right next bet.

- **[Interactive Widgets Framework](interactive-widgets-framework.md)** —
  ⚪ written up. A registry + sandboxed runtime + authoring UX so new interactive
  educational widgets (the thermo piston sim and successors) are easy to build and
  safe to render. Seeded by Cabinet Data Fidelity's M7-11 sandbox primitive;
  promote once that ships.
- **Mobile shell** — bottom tab bar shipped 2026-06-04 (#195 / `M5-01`).
  Remaining work for a proper proposal: route-level mobile layouts, PWA install,
  offline-tolerant question viewing.
- **AI tutor surface** — student-facing conversational help over the existing
  hint + explanation backends.
- **Accessibility pass** — WCAG 2.1 AA across the migrated V2 surfaces.
- **Performance budget** — route-level code-splitting, image/font optimisation.
