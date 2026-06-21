# WeeklyReportPanel — list-error state + skeleton loading

**Date:** 2026-06-10
**Classification:** Improve (polish)
**Initiative:** AI Surface Activation — polish pass (ASA-P2, daily plan 2026-06-10 PR 2)

## Summary

Completed the error-as-empty-state sweep on the teacher AI panels: a failed
weekly-report fetch used to render "No weekly summary yet. Generate one…",
inviting the teacher to regenerate a report that may already exist instead of
saying the server was unreachable. The panel now shows an explicit error line
with inline Retry, and loading uses a shape-matched report-card skeleton.

## Legacy reference

None — modern AI feature. Same SPA-specific failure mode as the sibling
panels: legacy server-rendered pages failed loudly; a SPA fetch failure can
look like clean data.

## What changed

- `frontend_modern/src/features/teacher/WeeklyReportPanel.tsx`
  - Destructured `isError` from `useWeeklyReport`. On list error:
    "Couldn't load the weekly summary just now." + inline **Retry**.
  - Empty state ("No weekly summary yet…") and the report card render only
    when `!isError`. The hook already maps a 404 to a successful `null`, so
    only real failures hit the error path.
  - New `ReportCardSkeleton` mirroring the report card (title + badge pill +
    3 body lines on the brand-tinted card), shown while loading.
  - Generate-error stays the inline rose box under the button — list-error
    and generate-error remain visually distinct. Badge logic untouched.
- `frontend_modern/src/features/teacher/WeeklyReportPanel.test.tsx`
  - 3 new cases: skeleton (not empty state) while loading; error + Retry
    (not empty state) on failed fetch; retry recovery.
- `docs/ai-features/polish-backlog.md` — dated entry; "Remaining gaps" now
  records the sweep as complete across all three panels.

No hook or backend changes.

## Tests

`npx vitest run WeeklyReportPanel` — 7 passed (4 existing incl. badges +
generate-error, 3 new). Lint + tsc clean.

## Next steps

Error-as-empty-state sweep is done. Remaining polish notes (cluster card
provenance field, ExplanationPanel badge consistency) stay in the backlog.
