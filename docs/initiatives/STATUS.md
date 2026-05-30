# Initiatives — Status Board

> The live priority order for long-horizon work. A routine with no higher-priority
> task advances the **top active initiative** here. See [`README.md`](README.md)
> for how. Keep this file short — one row per initiative.

**Last updated:** 2026-05-30

| Priority | Initiative | Status | Headline progress | Next increment |
|:--:|---|---|---|---|
| 1 | [V2 "Chalk & Unlock" design overhaul](2026-design-system-v2.md) | 🟢 Active | Foundation + shell + login + **home page** shipped & verified in Docker. Discovered question rendering (LaTeX/HTML/variables) is broken → new `M7` parity milestone. | `M7-01` — render question LaTeX + HTML (highest value); then `M4` dashboards |

## Legend

- 🟢 **Active** — being advanced now; pull its top increment.
- 🟡 **Paused** — intentionally on hold (reason in the doc).
- ⚪ **Proposed** — written up but not yet started.
- ✅ **Done** — North Star reached; keep for history.

## Backlog of future initiatives (proposed, not yet scoped)

These are candidate long-horizon goals. Promote one to its own doc when it
becomes the right next bet.

- **Mobile shell** — bottom tab bar, route-level mobile layouts, PWA install.
- **AI tutor surface** — student-facing conversational help over the existing
  hint + explanation backends.
- **Accessibility pass** — WCAG 2.1 AA across the migrated V2 surfaces.
- **Performance budget** — route-level code-splitting, image/font optimisation.
