# AIV-7 — `ProblemSetVersion`: deduplicated immutable content versions

**Date:** 2026-06-09
**Initiative:** Authoring Integrity & Versioning — Phase 3
**Classification:** New
**Depends on:** AIV-1 (snapshot), AIV-6 (re-sync)

## Summary

Per-assignment `assigned_content` snapshots — which AIV-1 through AIV-6 wrote one copy per assignment — are now promoted to a deduplicated, immutable `ProblemSetVersion` table. Every new (or re-synced) assignment pins a version FK. Identical content under the same set collapses into one row.

The legacy `Assignment.assigned_content` JSONField stays populated as a safety net so legacy readers (and untouched test data) keep working. A new helper `resolve_assignment_content(assignment)` is the single source of truth and is wired into the grader, the student serializer, drift detection, and the re-sync flow.

## Schema

- `ProblemSetVersion(problem_set FK, version_number, content_hash, content JSON, created_at, created_by)`
  - `unique_together = (problem_set, content_hash)` → dedup invariant
  - `version_number` is monotonic per parent set, assigned at mint time
  - **Immutable**: nothing in the codebase mutates a row after creation
- `Assignment.problem_set_version = FK(ProblemSetVersion, null=True, on_delete=PROTECT)`
- `Assignment.assigned_content` becomes the "legacy fallback" with a doc-only deprecation note

## New helpers (`apps/core/snapshots.py`)

- `_content_hash(snapshot)` — sha256 over the canonical (sorted-keys) JSON of the `questions` block. Ignores volatile fields so equivalent snapshots hash identically.
- `get_or_create_version_for(problem_set, *, created_by=None)` — idempotent factory; selects-for-update inside a transaction to keep dedup safe under concurrency.
- `resolve_assignment_content(assignment)` — returns `assignment.problem_set_version.content` if present, else falls back to `assigned_content`. Every snapshot reader routes through this.

## Capture sites (writers)

All three populate **both** the FK and the legacy JSONField:

- `AssignmentSerializer.create` (regular assign path)
- `_create_remedial_assignment` (auto-remedial path)
- `AssignmentViewSet.resync` (AIV-6 re-sync)

## Reader sites

- `apps/core/tasks.py grade_submission` — uses `resolve_assignment_content`
- `AssignmentDetailSerializer.to_representation` + `get_snapshot_drift` — uses `resolve_assignment_content`
- `AssignmentViewSet.resync_preview` + `resync` — uses `resolve_assignment_content`

## Migration

- `0025_problem_set_version.py` — schema (model + FK + indexes)
- `0026_backfill_problem_set_versions.py` — data: for each existing `Assignment` with `assigned_content` and no FK, find/create a `ProblemSetVersion` for that `(problem_set_id, content_hash)` pair (de-dup on the way in), then set the FK. Idempotent on re-runs.

## Tests (`apps/core/tests/test_problem_set_version.py`)

- **`get_or_create_version_for`**: mints v1 on first call; dedups on second; mints v2 after a live edit; per-set version_number scoping.
- **Capture**: `AssignmentSerializer.create` pins the FK; two assignments of the same set share one version row.
- **`resolve_assignment_content`**: prefers FK when both populated; falls back to legacy when FK is null.
- **Grader**: with `assigned_content=None` and only the FK populated, grading still scores against the frozen version content — proving the cutover works.

## Verify

- pytest: **85 passed** — AIV-7 suite + snapshot + grading + remedial + assignment-API + resync + drift + snapshot-view tests. No regressions.
- `manage.py check` clean.

## Next

- **AIV-8** — version history + diff UI on top of the new `ProblemSetVersion` rows.
