# M4-07a — Teacher dashboard panels → V2

**Classification:** Improve.

## Summary
Migrates the three remaining child panels of the Teacher Dashboard
(`ClassHealthPanel`, `WeeklyReportPanel`, `ClassroomCodeWidget`) from the
legacy `indigo`/`gray-*`/raw-status colours to V2 tokens + `Button` primitive.
The Teacher Dashboard host shell + `InterventionsPanel` are already V2, so the
page now reads as a single branded surface.

## Files changed
- `frontend_modern/src/features/teacher/ClassHealthPanel.tsx`
- `frontend_modern/src/features/teacher/WeeklyReportPanel.tsx`
- `frontend_modern/src/features/teacher/ClassroomCodeWidget.tsx`

## What changed
- Status dots: `bg-red-500` → `bg-rose-500`, `bg-yellow-400` → `bg-amber-400`,
  `bg-green-500` → `bg-emerald-500`. Matches the established AlertsPanel
  severity tones.
- Weekly summary surface: `bg-indigo-50/60` + indigo headings →
  `bg-brand-50/60` + `text-brand-800` on a `border-brand-100` shell.
- Join code chip: `bg-indigo-50 text-indigo-700` → `bg-brand-50 text-brand-800`
  with `ring-1 ring-brand-100`.
- All hand-rolled buttons → `Button` primitive (`variant="ghost"` for inline
  actions; `variant="brand"` for the empty-state generate CTA).
- Disclosure chevrons honour `motion-reduce:transition-none`.
- Disclosure toggle buttons gain a `focus-visible:ring-2 ring-brand-500` ring
  (previously had `focus:outline-none` with no replacement).

## What was preserved
- All data hooks (`useClassInsights`, `useWeeklyReport`,
  `fetchClassroomCodes`), mutations, refetch debouncing, the `setTimeout`
  delay for async server tasks, copy-to-clipboard behaviour.
- `InterventionsPanel` not touched (already V2, per plan).

## Continuous improvement
- Adds focus-visible rings to all three disclosure toggles + the copy code
  block — the legacy panels were not keyboard-reachable in a visible way.
- Honours `prefers-reduced-motion` on the chevron rotation.

## Verification
- `npm run type-check`, `npm run lint`, `npm run build`, `npm test` — all green.
- Grep `primary|indigo|blue-|gray-50|text-gray-` in the three files → 0.

## Next
- M4-07b Teacher assignment detail.
