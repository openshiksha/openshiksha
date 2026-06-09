# AIV-8 — Version history + diff UI

**Date:** 2026-06-09
**Initiative:** Authoring Integrity & Versioning — Phase 3
**Classification:** New
**Depends on:** AIV-7 (`ProblemSetVersion` model)

## Summary

Teachers can now browse the immutable version history for a problem set and diff any two versions. Builds directly on AIV-7's `ProblemSetVersion` table — the list is just that table sorted newest-first with an `assignment_count` annotation; the diff reuses AIV-6's `diff_snapshots` server-side helper so both surfaces share one source of truth.

## Backend

- `GET /api/v1/problem-sets/<id>/versions/` — returns `{problem_set_id, versions: [{id, version_number, content_hash, created_at, created_by_name, question_count, assignment_count}]}`. Annotated with `Count` over the reverse `assignments` relation so it's N+1-free.
- `GET /api/v1/problem-sets/<id>/versions/<version_pk>/diff/?against=<other_version_pk>` — structured diff between two versions of the same set. `against` defaults to the immediately-prior version (by `version_number`) when omitted.
- `ProblemSetVersionSummarySerializer` — lightweight row shape used by the list endpoint.

## Frontend

- `useProblemSetVersions` + `useVersionDiff` hooks
- `ProblemSetVersionsPage` — version timeline (newest-first), click-to-select target → click another row to select against → diff panel renders the structured diff summary
- `/teacher/problem-sets/:id/versions` route + a **View version history** button on `ProblemSetPreviewPage`

## Files

- `backend/openshiksha/apps/api/serializers/core.py` — `ProblemSetVersionSummarySerializer`
- `backend/openshiksha/apps/api/views/core.py` — `versions` + `version_diff` actions on `ProblemSetViewSet`
- `backend/openshiksha/apps/api/tests/test_problem_set_versions_api.py` (new) — 7 tests
- `frontend_modern/src/features/teacher/useProblemSetVersions.ts` (new)
- `frontend_modern/src/features/teacher/ProblemSetVersionsPage.tsx` (new)
- `frontend_modern/src/features/teacher/ProblemSetVersionsPage.test.tsx` (new) — 4 tests
- `frontend_modern/src/features/teacher/ProblemSetPreviewPage.tsx` — link to versions page
- `frontend_modern/src/App.tsx` — route + lazy import

## Verify

- pytest: 7 passed (list ordering, summary shape, assignment-count annotation, default `against`, explicit `against`, no-prior-version, cross-set 404)
- Vitest: 4 passed (newest-first list, two-click target+against selection, identical-content empty state, no-versions empty state)
- `type-check`, `lint --max-warnings 0`, `build` clean

## Closes Phase 3

This is the last increment of Authoring Integrity & Versioning. Together with Phase 1 (snapshot foundation) and Phase 2 (editable preview + drift surface), Phase 3 (re-sync + versions + history) delivers the initiative's full Definition of Done:

- Editing never silently rewrites assigned content (AIV-1/2)
- Editing is safe by construction and surfaced as such in the UI (AIV-3, AIV-4)
- Teachers can see what was assigned vs what the live set looks like now (AIV-5)
- Re-sync is opt-in, previewed, reversible (AIV-6)
- Assignments pin an immutable, deduplicated content version (AIV-7)
- Version history is auditable and diffable (AIV-8)
