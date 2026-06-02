# Initiatives — Status Board

> The live priority order for long-horizon work. A routine with no higher-priority
> task advances the **top active initiative** here. See [`README.md`](README.md)
> for how. Keep this file short — one row per initiative.

**Last updated:** 2026-06-01

| Priority | Initiative | Status | Headline progress | Next increment |
|:--:|---|---|---|---|
| 1 | [Cabinet Data Fidelity](cabinet-data-fidelity.md) (M7-03/06/08) | 🟢 Active | M7-04 envs, M7-05 tag-collision, M7-07 stem, M7-09 taxonomy all shipped 2026-05-31. Remaining: per-subpart widget type, inline images, expression coverage. | Closing batch of 5: M7-08, M7-06, M7-03a/b, fidelity-audit guard — see [2026-06-01-plan](../daily-plans/2026-06-01-plan.md) |
| 2 | [V2 "Chalk & Unlock" design overhaul](2026-design-system-v2.md) | 🟡 Paused | Foundation + shell + login + home shipped. Paused behind Cabinet Data Fidelity per 2026-05-30 user direction. | `M4` dashboards / M7-10 filter-sort, after fidelity closes |

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
- **Mobile shell** — bottom tab bar, route-level mobile layouts, PWA install.
- **AI tutor surface** — student-facing conversational help over the existing
  hint + explanation backends.
- **Accessibility pass** — WCAG 2.1 AA across the migrated V2 surfaces.
- **Performance budget** — route-level code-splitting, image/font optimisation.
