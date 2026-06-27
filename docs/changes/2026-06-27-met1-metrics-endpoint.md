# MET-1 — `prometheus-client` dep + env-gated `/metrics` endpoint

**Date:** 2026-06-27
**Initiative:** [Production Observability & Operational Readiness](../initiatives/2026-production-observability.md) — Batch 2 (Metrics & dashboards), increment 1 of 5
**Plan:** [2026-06-27-plan.md](../daily-plans/2026-06-27-plan.md)
**Classification:** New

## Summary

Adds the foundation of Observability Batch 2: a Prometheus text-exposition
endpoint at `/metrics/`, **strictly env-gated**. It returns `404` unless
`METRICS_ENABLED=true`, so default dev / test / CI behaviour is byte-for-byte
today's. When enabled it serves the process-global default registry — so the
runtime collectors prometheus_client auto-registers (process CPU/RSS, open fds,
Python GC) are exposed for free — plus an `openshiksha_build_info` gauge whose
labels (version / git sha / environment) pin a metrics series to a specific live
build (the same identity `/api/v1/version/` surfaces).

## What changed

- `backend/requirements.txt` — pin `prometheus-client==0.21.1` (the thin
  exposition lib, **not** `django-prometheus` which auto-patches and is always-on,
  violating the operability bar).
- `backend/openshiksha/settings/base.py` — `METRICS_ENABLED` (default `false`)
  and `METRICS_TOKEN` (optional bearer-token gate) settings.
- `backend/openshiksha/apps/core/metrics.py` — uses the default registry;
  `openshiksha_build_info` gauge refreshed at scrape time; `render_latest()` /
  `metrics_enabled()` helpers. A comment records the verified single-daphne-process
  assumption (no `PROMETHEUS_MULTIPROC_DIR` needed until multi-worker).
- `backend/openshiksha/apps/api/views/metrics.py` — cheap plain-Django
  (`csrf_exempt`, no DRF, no DB) `metrics_view`: `404` when disabled, `403` on a
  bad token (constant-time `hmac.compare_digest`), `200` exposition otherwise.
- `backend/openshiksha/urls.py` — mount `path("metrics/", ...)` next to the
  `/healthz/` + `/readyz/` probes.

## Exposure (verified)

The ingress routes only `/api`, `/django-admin`, `/static`, `/` — so top-level
`/metrics` is **not publicly routable**; it is reachable only in-cluster via the
`backend:8000` Service. The token gate is defence in depth. (No ingress path is
added for `/metrics`.)

## Operability bar

1. **Additive & env-gated** — `404` and invisible unless `METRICS_ENABLED=true`
   (`test_disabled_by_default_returns_404`).
2. **Probe-safe** — separate cheap path; liveness/readiness untouched.
3. **No secrets** — exposition is build identity + (later) aggregate counts only;
   optional token gate.
4. **No perf/offline regression** — backend/infra-only; no frontend change.
5. **Tested both ways** — gated-off (404) and gated-on (exposition + token gate).

## Tests

`backend/openshiksha/apps/api/tests/test_metrics_endpoint.py` (8 tests):
default 404; enabled returns valid Prometheus exposition (`# HELP`/`# TYPE`) with
`openshiksha_build_info`; build-info labels reflect `override_settings`; token
gate (missing / wrong / correct / unset).

## Migration notes

None — no model changes. To enable: set `METRICS_ENABLED=true` (and optionally
`METRICS_TOKEN=<random>`) in the prod secret; leave unset everywhere else.

## Next steps

- **MET-2** — business + queue-depth gauges (active assignments, grade-queue
  depth, users by role, classroom counts) via a scrape-time collector.
- **MET-3** — async-task health gauges from `django_celery_results.TaskResult`.
- **MET-4** — gated HTTP request count + latency histogram middleware.
- **MET-5** — Grafana starter dashboard + scrape runbook + ledger.
