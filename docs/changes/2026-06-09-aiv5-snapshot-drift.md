# AIV-5 — Assignment-level snapshot preview + drift banner

**Date:** 2026-06-09
**Initiative:** Authoring Integrity & Versioning — Phase 2
**Classification:** New
**Depends on:** AIV-1/2 (snapshot capture + readers)

## Summary

Teachers opening an assignment now see a collapsible **"What students see · snapshot"** section that renders the frozen `Assignment.assigned_content` through the same `QuestionCard` students use (locked, no input). When the live `ProblemSet` has moved past the snapshot, an amber drift banner explains the situation and deep-links to the editable live-set preview so the teacher can compare.

Backend ships:
- `apps.core.snapshots.snapshot_has_drifted(snapshot, problem_set)` — true iff the snapshot's `questions` block differs from a fresh one built from the live set.
- `snapshot_drift: bool` on `AssignmentDetailSerializer` — the teacher view reads this; the same payload's `problem_set.questions` is already the snapshot view from AIV-2b.

## Files

- `backend/openshiksha/apps/core/snapshots.py` — `snapshot_has_drifted`
- `backend/openshiksha/apps/api/serializers/core.py` — `snapshot_drift` field on `AssignmentDetailSerializer`
- `backend/openshiksha/apps/core/tests/test_snapshot_drift.py` (new) — 7 tests
- `frontend_modern/src/types/index.ts` — `Assignment.snapshot_drift?`, new `AssignmentDetail` interface
- `frontend_modern/src/features/teacher/useTeacherAssignmentDetail.ts` — types the meta query as `AssignmentDetail`
- `frontend_modern/src/features/teacher/AssignmentSnapshotPreview.tsx` (new)
- `frontend_modern/src/features/teacher/AssignmentSnapshotPreview.test.tsx` (new) — 4 tests
- `frontend_modern/src/features/teacher/TeacherAssignmentDetailPage.tsx` — renders the preview section

## Verify

- pytest: 16 passed (drift + snapshot + assignment-snapshot-view).
- Vitest: 65 passed across `src/features/teacher/`.
- `npm run type-check` clean; `npm run lint` clean (max-warnings 0); `npm run build` clean.

## Notes

- The teacher response keeps the existing student-safe shape — `correct_answer` is still stripped. Teachers needing answer keys still go through the question bank / question editor; this view is "see what students see".
- Drift detection ignores volatile fields (`captured_at`, `problem_set_title`) so renaming the set or re-snapshotting doesn't false-positive.

## Next

- **Phase 3** — AIV-6 (guarded re-sync of an assignment to the latest content, with a preview of the blast radius) → AIV-7 (`ProblemSetVersion` model; assignments pin a version) → AIV-8 (version history + audit UI).
