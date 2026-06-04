# 2026-06-03 — Parent Dashboard + Insights migrated to V2

## Summary
Migrated all parent-role surfaces to V2 "Chalk & Unlock":
`ParentDashboard.tsx`, `ParentInsightsLandingPage.tsx`, `ParentInsightsPage.tsx`,
and the shared `NarrativeCard`, `AlertsPanel`, `HomeActivitiesPanel` components.

## Classification
Improve — reskin only. Data hooks, routes, role guards untouched.

## What changed
- All `indigo-*`, `text-gray-*`, `border-gray-*`, `bg-gray-50`, `red-*`, `green-*`,
  `blue-*` classes replaced with `brand-*`/`ink-*`/`rose-*`/`emerald-*`/`amber-*`.
- Headings now `<SectionHeading>` (font-display Fraunces).
- Cards now `<Card>` / `.os-card`.
- Status pills use `<Badge>` with `success`/`attention`/`urgent`/`brand` tones —
  the dashboard now exposes an Overdue badge (previously labeled "Pending").
- Active tab gets the chalk-underline treatment + focus-visible ring.
- Empty states swapped for `<EmptyState>` keyhole motif.
- Sparkline-style proficiency bars recoloured to `emerald/amber/rose` semantic
  thresholds on warm `ink-100` track.
- `motion-reduce:transition-none` added to every transition for a11y.

## Tests
- `npm run type-check` green
- `npm run lint` green
- `npm test -- --run` 84/84 (incl. `AlertsPanel.test.tsx`, `HomeActivitiesPanel.test.tsx` —
  `data-severity` and `data-celebrate` query hooks preserved)
- `npm run build` green

## Verify
Log in as `parent_demo` / `demo1234`. Open `/parent`, then `/parent/insights`,
then a child insights page.

## Next
PRs 3–5 will migrate Admin, Proficiency cluster, and Assignment/SRS surfaces.
