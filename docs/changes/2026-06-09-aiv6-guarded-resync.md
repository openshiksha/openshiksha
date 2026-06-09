# AIV-6 — Guarded assignment re-sync

**Date:** 2026-06-09
**Initiative:** Authoring Integrity & Versioning — Phase 3
**Classification:** New
**Depends on:** AIV-1 (snapshot field), AIV-5 (drift detection)

## Summary

Teachers can now **opt into adopting** the latest live content for an existing assignment, with a blast-radius preview shown first and re-grading only on confirm. The action is fully reversible — the prior snapshot is archived in a new `AssignmentSnapshotHistory` model that the **Undo last update** affordance restores from.

## Backend

- `AssignmentSnapshotHistory(assignment, content, replaced_at, replaced_by)` — one row per superseded snapshot. Newest-first ordering; undo pops the head.
- `apps.core.snapshots.diff_snapshots(old, new)` — structured diff: `questions_added` / `questions_removed` / `answer_changes` (carry `before`+`after` for each subpart) / `content_changes` (cosmetic-only edits).
- `GET /api/v1/assignments/<id>/resync-preview/` — returns `{has_drift, diff, affected: {submitted_count, graded_count, regrade_on_apply}}`. Read-only.
- `POST /api/v1/assignments/<id>/resync/` — atomic: archive prior snapshot, swap to the fresh one, drop stale ticks for graded submissions, queue `grade_submission` per submission. Only re-grades when `answer_changes` is non-empty.
- `POST /api/v1/assignments/<id>/undo-resync/` — restores the most recent history row's content and removes the row. 404 when no history.
- `AssignmentDetailSerializer.has_resync_history` — flag so the UI knows when to offer Undo.

## Frontend

- `useAssignmentResync.ts` — `useResyncPreview`, `useApplyResync`, `useUndoResync`.
- `ResyncAssignmentModal.tsx` — confirmation modal that loads the preview lazily, summarises the diff, and warns about the re-grade count when answers changed. Apply button disabled when nothing has drifted.
- `AssignmentSnapshotPreview.tsx` — the AIV-5 drift banner now mounts the modal via an **Update this assignment…** button; an **Undo last update** bar appears under the toggle when `has_resync_history` is true.

## Files

- `backend/openshiksha/apps/core/models.py` — new `AssignmentSnapshotHistory`
- `backend/openshiksha/apps/core/migrations/0024_assignment_snapshot_history.py` — schema
- `backend/openshiksha/apps/core/snapshots.py` — `diff_snapshots`
- `backend/openshiksha/apps/api/views/core.py` — three new actions on `AssignmentViewSet`
- `backend/openshiksha/apps/api/serializers/core.py` — `has_resync_history` field
- `backend/openshiksha/apps/api/tests/test_assignment_resync.py` (new) — 12 tests
- `frontend_modern/src/types/index.ts` — `Assignment.has_resync_history?`
- `frontend_modern/src/features/teacher/useAssignmentResync.ts` (new)
- `frontend_modern/src/features/teacher/ResyncAssignmentModal.tsx` (new)
- `frontend_modern/src/features/teacher/ResyncAssignmentModal.test.tsx` (new) — 5 tests
- `frontend_modern/src/features/teacher/AssignmentSnapshotPreview.tsx` — drift banner gains the action + undo bar
- `frontend_modern/src/features/teacher/AssignmentSnapshotPreview.test.tsx` — coverage for the new affordances
- `frontend_modern/src/features/teacher/TeacherAssignmentDetailPage.tsx` — passes new props through

## Verify

- pytest: 12 passed (diff helper + preview + apply + undo paths). Existing snapshot/drift/grading suites still green.
- Vitest: 12 passed across the two affected components; full teacher suite stays green.
- `type-check`, `lint --max-warnings 0`, `build` all clean.

## Next

- AIV-7 — promote per-assignment snapshots to a deduplicated, immutable `ProblemSetVersion` model.
