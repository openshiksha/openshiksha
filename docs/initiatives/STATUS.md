# Initiatives — Status Board

> The live priority order for long-horizon work. A routine with no higher-priority
> task advances the **top active initiative** here. See [`README.md`](README.md)
> for how. Keep this file short — one row per initiative.

**Last updated:** 2026-06-02 (post-batch: M1-06, M2-03, M3-02, M4-01, M4-03, M7-02, M7-05 all shipped)

| Priority | Initiative | Status | Headline progress | Next increment |
|:--:|---|---|---|---|
| 1 | [V2 "Chalk & Unlock" design overhaul](2026-design-system-v2.md) | 🟢 Active | **M1 complete**, shell + login + home + register + Student/Teacher dashboards all on V2. **M7-02 (variable substitution) and M7-05 (seed idempotency) shipped today** — `{{var}}` tokens substitute for students; `seed_demo_data` runs cleanly against cabinet-imported DB and now provisions all 5 demo accounts. 6 M4 page-groups remain (Parent, Admin, Assignment/Drill, Proficiency/Browse, Teacher Authoring, Profile). | `M4-05` Assignment detail + SRS drill (highest student traffic) OR `M4-02` Parent dashboard |
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
- **Mobile shell** — bottom tab bar, route-level mobile layouts, PWA install.
- **AI tutor surface** — student-facing conversational help over the existing
  hint + explanation backends.
- **Accessibility pass** — WCAG 2.1 AA across the migrated V2 surfaces.
- **Performance budget** — route-level code-splitting, image/font optimisation.
