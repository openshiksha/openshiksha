# ASA-5 — Teacher MisconceptionClustersPanel (first consumer of /ai/misconception-clusters/)

**Date**: 2026-06-09
**Classification**: New
**Initiative**: AI Surface Activation (ASA-5)

## Summary

`/ai/misconception-clusters/` (list + async refresh, teacher-scoped, fully
built and tested on the backend) had zero frontend consumers. The teacher
dashboard's per-room insights disclosure now includes a "Class Misconceptions"
panel: aggregated misconception patterns across the class, each with affected
student count, a sample diagnosis, and a concrete remediation tip.

## Legacy reference

Legacy `edge/` gave teachers aggregate scores per class — never anything
diagnostic. Clusters give the *why* behind low scores; legacy never attempted
this. Internal pattern reference: `InterventionsPanel` (collapsible section,
per-room scoping, refresh action, lazy fetch).

## What changed

- `frontend_modern/src/features/teacher/useMisconceptionClusters.ts` (new):
  list query (`?subject_room=<id>`, handles paginated + plain shapes, lazy via
  `enabled`) + refresh mutation (`POST /refresh/` → 202; delayed invalidate
  ~2.5 s later to pick up the async recompute, same convention as
  `useGenerateInterventions`).
- `frontend_modern/src/features/teacher/MisconceptionClustersPanel.tsx` (new):
  collapsed by default; count badge in the header; per-cluster card renders
  exactly what the serializer exposes (`misconception_label`, `student_count`
  with attention-tone badge at ≥3, `sample_diagnosis`,
  `sample_remediation_tip`, `occurrence_count`, `last_seen`, `refreshed_at`).
  Refresh button → "Recomputing…" status note; inline error on failure.
  No AI/stub badge — the cluster serializer carries no `model_used` field
  (clusters are aggregations of per-student diagnoses).
- `frontend_modern/src/features/teacher/TeacherDashboard.tsx`: panel mounted
  in `RoomInsights` between `InterventionsPanel` and `QuestionQualityPanel` —
  inside the existing lazy disclosure, so no extra fetches on first paint.

## Tests

`npx vitest run MisconceptionClustersPanel` — 5 tests passing: collapsed by
default + fetch-on-open (loading state asserted via deferred promise);
populated cluster details; explanatory empty state; refresh queued +
recompute status; inline refresh error. Role gating is server-side
(teacher-scoped queryset) and the panel only mounts on the teacher dashboard.

`npx tsc --noEmit`, `npm run lint`, `npm run build` clean. No backend changes.

## Migration notes

None — frontend only.

## Next steps

Batch ASA-1..5 complete. ASA-6 (assignment-draft builder UI) and ASA-7
(open-response grading UI) are the remaining dark surfaces — each a
batch-anchor for a future run. ASA-9 (backend same-day review idempotency)
remains in the backlog.
