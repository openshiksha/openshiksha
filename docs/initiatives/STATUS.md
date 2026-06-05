# Initiatives — Status Board

> The live priority order for long-horizon work. A routine with no higher-priority
> task advances the **top active initiative** here. See [`README.md`](README.md)
> for how. Keep this file short — one row per initiative.

**Last updated:** 2026-06-04 — V2 milestones largely closed. Today's second batch shipped M7-03 remaining (#197), M2-02 (#198), M3-03 (#199), Enquire-success fix (#200), M5-02 (#201), M6-01 (#202), M6-03 (#203) and M7-04 (this doc PR). See [legacy-feature-parity.md](legacy-feature-parity.md) for the new parity audit.

| Priority | Initiative | Status | Headline progress | Next increment |
|:--:|---|---|---|---|
| 1 | [V2 "Chalk & Unlock" design overhaul](2026-design-system-v2.md) | 🟢 Active | **M1, M2 (01+02+03), M3 (01+02+03+04), M4 (all), M5-01, M6-01, M6-02, M6-03 infra, M7-01/02/03/04/05 done.** The product wears one branded language end-to-end; the legacy `primary` blue is gone; tables overflow safely on mobile; the navbar is a11y-clean; a skip-link lands keyboard users on `<main>`; the AddToProblemSet dialog has full modal semantics; visual-regression spec is in place (baselines pending CI seed). **Remaining:** `M5-02` follow-ups (touch-target audit, PWA), `M6-03` baseline activation (commit Linux PNGs and unskip), `M7-03` Question Bank chapter-filter UI + assignment-list filters. | Pick from: **commit `M6-03` Linux baselines via CI** (small, unblocks visual-regression gating); **`ADMINS` env-var wiring** so concierge enquiry email stops no-op'ing (5 lines, called out in the parity audit); **Question Bank chapter-filter UI** (final M7-03 slice); or promote the **Accessibility Pass** backlog item to its own initiative now that a baseline a11y audit exists. |
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
- **Accessibility pass** — WCAG 2.1 AA across the migrated V2 surfaces. A
  focused baseline pass landed 2026-06-04 (M6-01 #202) — skip link, dialog
  semantics, image alts. Promote to its own initiative when ready for a
  full audit (keyboard walkthrough, screen-reader spot-check, axe-core CI).
- **Performance budget** — route-level code-splitting, image/font optimisation.
