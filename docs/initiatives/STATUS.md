# Initiatives — Status Board

> The live priority order for long-horizon work. A routine with no higher-priority
> task advances the **top active initiative** here. See [`README.md`](README.md)
> for how. Keep this file short — one row per initiative.

**Last updated:** 2026-06-04 (planned: final M4 batch — M4-06b browse/learn slice + M4-07 teacher authoring; closes M4. See `docs/daily-plans/2026-06-04-plan.md`)

| Priority | Initiative | Status | Headline progress | Next increment |
|:--:|---|---|---|---|
| 1 | [V2 "Chalk & Unlock" design overhaul](2026-design-system-v2.md) | 🟢 Active | **M1 complete**, shell + login + home + register + Student/Teacher dashboards all on V2. **M7-02 (variable substitution) and M7-05 (seed idempotency) shipped today** — `{{var}}` tokens substitute for students; `seed_demo_data` runs cleanly against cabinet-imported DB and now provisions all 5 demo accounts. **2026-06-03 batch shipped** (PRs #180–185): Profile, Parent, Admin, Proficiency-cluster, Assignment/SRS all on V2. Only the Browse/LearningPath slice (M4-06b) + Teacher Authoring (M4-07) remain — and most of M4-07 (ProblemSet/Assignment/QuestionBank pages) is already V2-native, leaving just 9 files. **2026-06-04 batch planned** to migrate all of them and **close M4**. | Execute `docs/daily-plans/2026-06-04-plan.md`: `M4-06b-i` → `M4-06b-ii` → `M4-07a` → `M4-07b` → `M4-07c` (lowest-risk-first). After: M6-02 (retire `primary`) / M5 mobile. |
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
