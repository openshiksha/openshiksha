# PERF-03 — Route-level `React.lazy` code-splitting

**Date:** 2026-06-07
**Initiative:** Performance Budget
**Classification:** Improve

## Summary

The big entry-chunk cut. Converts every route page in `src/App.tsx` to
`React.lazy` behind one top-level `<Suspense>` so the K-12 student opening
`/login` on a budget Android phone no longer downloads the teacher authoring
surface, parent insights, admin classroom manager, or the dev-only widget
playground / design-system page.

Eager imports (small, on the critical first-paint path):
`LoginPage`, `RegisterPage`, `RegisterSchoolPage`, `RegisterOpenPage`,
`HomePage`, `AppShell`, `ProtectedRoute`, `NotFoundPage`, `LoadingSpinner`,
`ErrorBoundary`, `UserRole`.

Lazy imports (everything else — 22 route pages):
`StudentDashboard`, `AssignmentDetailPage`, `ProficiencyPage`,
`LearningPathPage`, `SRSDrillPage`, `BrowsePage`, `BrowsePracticePage`,
`ProfilePage`, `TeacherDashboard`, `CreateAssignmentPage`, `CreateQuestionPage`,
`CreateProblemSetPage`, `ProblemSetPreviewPage`, `TeacherAssignmentDetailPage`,
`QuestionBankPage`, `ParentDashboard`, `ParentInsightsPage`,
`ParentInsightsLandingPage`, `AdminDashboard`, `ClassroomManagePage`,
`EnquirePage`, `DesignSystemPage`, `WidgetDevPage`.

A typed `lazyNamed(loader, name)` helper preserves component props through the
default-export shim, so `<CreateQuestionPage editMode={true} />` type-checks
correctly.

## Results — entry chunk

| Stage                                          | Size      | Gzip      |
| ---------------------------------------------- | --------- | --------- |
| Baseline (no chunking)                         | 855.15 kB | 247.44 kB |
| Post-PERF-01 (vendor split)                    | 353.05 kB |  91.53 kB |
| **Post-PERF-03 (this PR — route lazy)**        | **131.41 kB** | **40.98 kB** |

That's an 84% drop in entry-JS gzip from baseline. Per-route chunks land
between 1–32 kB each so a user only pays for the page they actually visit.

## Why a single top-level `<Suspense>`

One boundary, one `LoadingSpinner` fallback — there's no need for per-route
suspense because every route already mounts inside `AppShell` (or is a thin
auth page). The fallback briefly flashes during chunk fetch and resolves on
arrival. The existing `ErrorBoundary` continues to wrap everything.

## Tests

- `npm run type-check` — green (the `lazyNamed` helper's conditional return
  type preserves component prop shapes through the lazy boundary).
- `npm run lint` — green.
- `npm test -- --run` — 31 files / 194 tests pass.
- `npm run build` — green; emits 23 per-route chunks + the shrunken entry.

## Next steps

- PERF-04: lazy-load KaTeX behind `RichContent` so non-math routes never pay
  for the 257 kB `vendor-katex` chunk.
- PERF-06: lock the post-cut size in with a CI bundle-size budget guard.
