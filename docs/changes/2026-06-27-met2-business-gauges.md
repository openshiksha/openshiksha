# MET-2 — Business & queue-depth gauges (on-scrape collector)

**Date:** 2026-06-27
**Initiative:** [Production Observability & Operational Readiness](../initiatives/2026-production-observability.md) — Batch 2, increment 2 of 5
**Plan:** [2026-06-27-plan.md](../daily-plans/2026-06-27-plan.md)
**Classification:** New

## Summary

Adds a `BusinessMetricsCollector` (the prometheus_client custom-collector
protocol) that runs read-only `COUNT` queries **at scrape time** and yields the
product/operational gauges that actually predict an OpenShiksha incident. It
registers on the default registry **lazily, on the first real (enabled) scrape**,
so no DB work happens — and the collector isn't even registered — while the
endpoint is disabled (it 404s before the collector is touched).

## Gauges

| Metric | Meaning |
|--------|---------|
| `openshiksha_assignments_active` | Assignments open (not closed) and not past due |
| `openshiksha_submissions_pending_grading` | Submitted submissions awaiting a grade — **grade-queue depth** |
| `openshiksha_users{role=...}` | Accounts grouped by role |
| `openshiksha_classrooms` | Total classrooms |
| `openshiksha_subjectrooms` | Total subject rooms |

Names follow Prometheus idiom (no `_total` suffix — that suffix is the *counter*
convention; these are gauges).

## Why on-scrape (not event counters)

Gauges computed lazily on each scrape are stateless: no cross-process
aggregation, no drift — the right pattern for "current size of X" signals. Each
is a single indexed `COUNT` (no joins, no N+1) so a scrape stays cheap. The
predicates reuse the product definitions: active = `closed_at IS NULL AND
due_at >= now` (mirrors `Assignment.status`); grade-queue = `submitted_at NOT
NULL AND score IS NULL`.

## Resilience

`collect()` wraps the queries in a `try/except`: a DB hiccup mid-scrape degrades
to "no business gauges this scrape" (build_info + runtime series still serve)
rather than 500-ing the endpoint.

## Tests

`backend/openshiksha/apps/core/tests/test_metrics_business.py` (5 tests): seeds a
small graph, scrapes `/metrics`, asserts active-assignments excludes a closed
one, grade-queue depth excludes a graded submission, users-by-role counts,
classroom/subjectroom totals, and build_info still rides alongside. (The grading
post_save signal auto-grades on submit under eager Celery, so the pending state
is forced via `.update()` which bypasses the signal.) Gated-off (404) path is
covered by MET-1's `test_metrics_endpoint.py`.

## Migration notes

None — no model changes.

## Next steps

- **MET-3** — async-task health gauges from `django_celery_results.TaskResult`.
- **MET-4** — gated HTTP request count + latency histogram middleware.
- **MET-5** — Grafana starter dashboard + scrape runbook + ledger.
