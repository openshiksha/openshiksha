# MET-3 — Async-task health gauges from `TaskResult` (on-scrape)

**Date:** 2026-06-27
**Initiative:** [Production Observability & Operational Readiness](../initiatives/2026-production-observability.md) — Batch 2, increment 3 of 5
**Plan:** [2026-06-27-plan.md](../daily-plans/2026-06-27-plan.md)
**Classification:** New

## Summary

Adds a `TaskMetricsCollector` that derives Celery health on-scrape from the
already-installed `django_celery_results.TaskResult` table. Celery runs as a
**separate worker process**, so in-worker counters can't be scraped from the web
process without a pushgateway/second exporter (out of scope per the operability
bar) — reading the DB the workers already write to is the cheap, correct path.

## Gauges (24h window by `date_created`)

| Metric | Meaning |
|--------|---------|
| `openshiksha_celery_tasks{status=...}` | Task counts by status (SUCCESS/FAILURE/STARTED/…) |
| `openshiksha_celery_oldest_pending_seconds` | Age of the oldest non-terminal task (`0` when none) — async grade-queue-staleness analogue |

## Result-backend gate (honest no-op, not a false zero)

The **default** `CELERY_RESULT_BACKEND` is **Redis**, where `TaskResult` stays
empty — emitting task gauges then would be a *misleading constant zero*. So
`_celery_results_in_db()` gates the whole collector: the gauges appear **only**
when `CELERY_RESULT_BACKEND` is the database backend (`django-db`). Flipping the
backend lights them up automatically; until then MET-3 is a documented no-op.
(Operators who want these metrics set `CELERY_RESULT_BACKEND=django-db` — noted
in the MET-5 runbook.)

## Resilience

Like MET-2, `collect()` is wrapped in `try/except` so a DB hiccup degrades to
"no celery gauges this scrape" rather than 500-ing the endpoint.

## Tests

`backend/openshiksha/apps/core/tests/test_metrics_tasks.py` (4 tests): with the
django-db backend, counts by status (SUCCESS=2, FAILURE=1) and a positive
oldest-pending age (a backdated STARTED row, set via `.update()` since
`date_created` is `auto_now_add`); oldest-pending reads `0` when none pending;
and with the default Redis backend the gauges are **absent** even if rows exist
(the honesty guard).

## Migration notes

None — `django_celery_results` is already installed and migrated.

## Next steps

- **MET-4** — gated HTTP request count + latency histogram middleware.
- **MET-5** — Grafana starter dashboard + scrape runbook + ledger.
