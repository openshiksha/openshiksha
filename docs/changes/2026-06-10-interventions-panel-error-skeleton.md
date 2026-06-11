# InterventionsPanel — list-error state + skeleton loading

**Date:** 2026-06-10
**Classification:** Improve (polish)
**Initiative:** AI Surface Activation — polish pass (ASA-P1, daily plan 2026-06-10 PR 1)

## Summary

Fixed the "error masquerades as all-clear" anti-pattern on the teacher
dashboard's `InterventionsPanel`: a failed list fetch used to render the empty
state ("No struggling students flagged yet"), telling a teacher nobody needs
help when the server was simply unreachable. The panel now shows an explicit
error line with an inline Retry, and loading uses shape-matched skeleton cards
instead of a bare text line.

## Legacy reference

None — the interventions panel is a modern AI feature. The anti-pattern is an
SPA-specific failure mode: legacy server-rendered pages failed loudly with a
500 page; a SPA fetch failure can silently look like clean data.

## What changed

- `frontend_modern/src/features/teacher/InterventionsPanel.tsx`
  - Destructured `isError` / `refetch` from `useInterventions`.
  - On list error: "Couldn't load suggestions just now." + inline **Retry**
    button (exact recipe from `MisconceptionClustersPanel`, PR #291).
  - Empty state and suggestion cards now render only when `!isError`.
  - New `SuggestionCardSkeleton` mirroring the `SuggestionCard` layout
    (name/meta lines, priority pill, badge + strategy lines, chapter chips),
    rendered twice while loading. Uses the shared `Skeleton` primitive.
- `frontend_modern/src/features/teacher/InterventionsPanel.test.tsx`
  - 3 new cases: skeletons (not empty state) while loading; error + Retry
    (not empty state) on failed fetch; retry recovery to real data.
- `docs/ai-features/polish-backlog.md` — dated entry added; `InterventionsPanel`
  removed from "Remaining gaps".

No hook changes needed — `useQuery` already exposes `isError`/`refetch`.
No backend changes.

## Tests

`npx vitest run InterventionsPanel` — 10 passed (7 existing incl. the
generate-error path, 3 new). `npm run lint` + `npx tsc --noEmit` clean.

## Next steps

`WeeklyReportPanel` gets the identical treatment in the next PR of this batch
(ASA-P2) — it is the last panel with the error-as-empty-state pattern.
