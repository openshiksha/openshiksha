# Class Misconception Insights

**Category:** Smart Analytics & Insights (Teacher AI Assistant)
**Status:** Shipped (2026-05-30)
**Branch / PR:** `ai/2026-05-30-class-misconception-insights`

## Problem it solves

The Intelligent Hint System (#102) generates a `StudentMisconception` row every
time a student gets a question wrong, capturing *why* they were wrong (e.g.
"sign error on subtraction"). That signal is rich per-student, but a teacher
looking at their class doesn't want to scroll through 30 individual
misconception rows — they want to see, "12 of my students share this same
misunderstanding right now, and I should re-teach it on Monday."

This feature aggregates the existing per-student misconceptions into
**class-level clusters**, surfacing the patterns worth a teacher's
intervention.

## How it works (technical)

1. **Aggregation** (`analytics.cluster_misconceptions_for_subject_room`)
   - Look at `StudentMisconception` rows for students enrolled in the
     `SubjectRoom`, detected within the last `CLUSTER_LOOKBACK_DAYS` (default
     30 days).
   - Normalise each `misconception_label` (lowercase, collapse whitespace,
     strip trailing punctuation) so trivially-different LLM outputs collapse
     onto the same cluster.
   - Group by normalised label, tracking distinct `student_count` and total
     `occurrence_count`.
   - Drop clusters below `CLUSTER_MIN_STUDENTS` (default 2). One student
     stumbling is not a class-level signal.
   - Keep a representative `sample_diagnosis` + `sample_remediation_tip` from
     the most recent underlying record so the dashboard can render
     actionable prose without a second LLM call.

2. **Persistence** (`ClassMisconceptionCluster` model)
   - One row per `(subject_room, misconception_label)`.
   - Snapshot semantics: `refresh_class_misconception_clusters` deletes the
     room's existing rows and replaces them — clusters whose underlying
     misconceptions have aged out of the window correctly disappear.

3. **API** (`/api/v1/ai/misconception-clusters/`)
   - `GET /` — teacher's clusters across all rooms they teach
   - `GET /?subject_room=<id>` — filter by room
   - `GET /<id>/` — single cluster
   - `POST /refresh/` — queue async recompute for a room the teacher owns
   - Strict teacher-only scoping enforced in the queryset.

## Models / APIs created

- `openshiksha.apps.ai.models.ClassMisconceptionCluster`
- Migration `0008_classmisconceptioncluster`
- `analytics.cluster_misconceptions_for_subject_room`,
  `analytics._normalise_misconception_label`
- `tasks.refresh_class_misconception_clusters`
- `views.ClassMisconceptionClusterViewSet`
- `serializers.ClassMisconceptionClusterSerializer`,
  `serializers.TriggerMisconceptionClusterSerializer`
- 15 tests in `tests/test_misconception_clusters.py`

## User impact

- **Teachers** — a single, ranked view of the most common conceptual errors
  in their class right now, with a sample diagnosis and remediation tip
  attached. Lets them decide *what to reteach* without trawling per-student
  data.

## Future enhancements

- **Semantic clustering** — today we collapse near-duplicate labels
  case-insensitively; tomorrow we could embed and cluster semantically so
  "off-by-one in indexing" and "starts counting from 1 not 0" merge.
- **Frontend dashboard card** — surface the top-3 clusters on the teacher
  dashboard with a one-click "create remedial assignment" CTA. This PR is
  backend-only; frontend lives in the V2 design overhaul.
- **Trend over time** — turn the snapshot into a time series so a teacher
  can see which misconceptions they've successfully retired vs. those that
  keep coming back.

## Dependencies

- Builds on `StudentMisconception` (PR #102 — Intelligent Hint System).
  Without that pipeline producing misconception rows, this clustering has
  no input.
