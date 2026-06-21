# AIV-3a — Edit-safety read flags

**Date:** 2026-06-08
**Initiative:** Authoring Integrity & Versioning — Phase 1
**Classification:** New
**Depends on:** AIV-1 conceptually (informs the UX that snapshots make editing safe)

## Summary

Add read-only `assigned_count` and `has_graded_submissions` to `ProblemSetSerializer` and `QuestionSerializer`. These flags exist purely to drive the **AIV-3b** teacher edit-safety banner — they do not gate writes. Integrity is already guaranteed by AIV-1/2 snapshots.

Queryset annotations (`Count` + `Exists`) are applied in `ProblemSetViewSet.get_queryset` and `QuestionViewSet.get_queryset` so list endpoints stay N+1-free. The serializer falls back to a per-row query when the annotation isn't present (e.g. POST response on a freshly created row).

## Files

- `api/serializers/core.py` — flags on `ProblemSetSerializer` + `QuestionSerializer`
- `api/views/core.py` — annotations on both viewset querysets
- `api/tests/test_edit_safety_flags.py` (new) — 5 tests

## Verify

- pytest: 40 passed (edit-safety + problemset + assignment tests)

## Next

- AIV-3b — non-blocking edit-safety banner in the teacher edit UI
