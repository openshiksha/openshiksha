# M4-06b-i — Browse cluster → V2

**Classification:** Improve.

## Summary
Migrates the student "browse the question bank and practice" slice
(`BrowsePage`, `BrowsePracticePage`) from the legacy `primary`/`indigo`/cold-gray
template to the V2 "Chalk & Unlock" tokens + `src/shared/ui` primitives. Closes
half of the deferred M4-06b in the V2 initiative.

## Files changed
- `frontend_modern/src/features/student/BrowsePage.tsx`
- `frontend_modern/src/features/student/BrowsePracticePage.tsx`

## What changed
- Page chrome composes `SectionHeading` (eyebrow + Fraunces title), `Select`
  fields (for board/grade filters), `os-card` containers, `Button`
  (`variant="brand"`), `Badge` (`tone="brand"` for the per-chapter question
  count), and `EmptyState` (keyhole motif) for the no-results surface.
- Table chrome moved from `bg-gray-50`/`text-gray-*` to warm `ink-*` tones with
  `brand-50/40` hover rows.
- `BrowsePracticePage` reuses the same primitives; `QuestionCard` is left
  untouched (already V2 since #185 / M4-05) per the daily plan's scope guard.
- Empty/error/submitted states all routed through the primitives so they share
  the system's keyhole motif and warm paper surface.

## What was preserved
- Data hooks (`useBrowseChapters`, the inline `useBrowsePractice` query),
  routes, role guards, and props — reskin only, no logic refactor.
- `QuestionCard` (per plan, untouched here; lives under M4-05).
- The (currently no-op) filter wiring — fixing the actual filtering is M7-03,
  out of scope for the V2 reskin.

## Continuous improvement
- Page-level filter chrome is now a single `.os-card` row + `Select`
  primitives, replacing two hand-rolled `<select>` blocks with focus-ring
  classes spelled out by hand. The Select primitive already carries
  focus-visible + AA labels.

## Verification
- `npm run type-check`, `npm run lint`, `npm run build`, `npm test` — all green.
- Grep `primary|indigo|blue-|gray-50|text-gray-` in both files → 0 matches.

## Next
- M4-06b-ii Learning Path + Videos.
- M7-03 Browse filter wiring (the controls don't currently filter results).
