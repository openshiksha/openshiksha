# M4-06b-ii — Learning Path + Videos → V2

**Classification:** Improve.

## Summary
Migrates `LearningPathPage` and `VideosPanel` to V2 tokens + `src/shared/ui`.
The path step indicators now use the brand "unlock" motif — completed steps are
emerald check marks, the up-next step is a brand-orange unlocked keyhole on a
`brand-50` shelf, and future steps are muted `ink-300` locked keyholes connected
by a vertical `ink-100` rail.

## Files changed
- `frontend_modern/src/features/student/LearningPathPage.tsx`
- `frontend_modern/src/features/student/VideosPanel.tsx`

## What changed
- `LearningPathPage` composes `SectionHeading` (eyebrow "Unlock your next
  chapter"), `EmptyState`, `Badge` (`tone="brand"` for the "Up next" pill),
  and `os-card` for path containers; progress bar uses `bg-brand-600` on
  `bg-ink-100` with `role="progressbar"` aria attrs.
- Step rows: unlocked/locked keyhole glyphs (inline SVG) replace the legacy
  numbered chips; vertical rail connecting steps for the "path" feel.
- `VideosPanel`: `os-card` shell, branded watch affordance (`text-brand-700`),
  `ink-*` text, focus-visible ring on the disclosure button.

## What was preserved
- Data hooks (`useLearningPaths`, `useChapterVideos`), props, conditional
  rendering, iframe embed configuration — reskin only.

## Continuous improvement
- Adds an aria-labelled `progressbar` to the path summary (previously a styled
  div with no semantic role).
- The Up-Next/Locked/Completed status indicators are now visually distinct in
  shape (keyhole vs check vs lock) so the system reads through colourblind
  modes as well, not only by colour.

## Verification
- `npm run type-check`, `npm run lint`, `npm run build`, `npm test` — all green.
- Grep `primary|indigo|blue-|gray-50|text-gray-` in both files → 0 matches.

## Next
- M4-07a Teacher dashboard panels.
