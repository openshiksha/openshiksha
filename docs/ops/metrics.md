# Metrics & dashboards runbook

OpenShiksha exposes Prometheus metrics at **`/metrics`** (Observability Batch 2,
MET-1..5). Everything here is **additive and env-gated**: with the defaults below,
the endpoint 404s and behaviour is byte-for-byte today's.

## Enabling

Metrics are **off by default**. To turn them on (in-cluster prod):

| Env var | Default | Effect |
|---------|---------|--------|
| `METRICS_ENABLED` | `false` | `true` makes `/metrics` serve (otherwise it 404s). |
| `METRICS_TOKEN` | `""` (unset) | When set, `/metrics` requires `Authorization: Bearer <token>`; otherwise 403. Defence in depth on top of the network boundary. |
| `CELERY_RESULT_BACKEND` | `redis://…` | The MET-3 Celery gauges only appear when this is the **`django-db`** backend (see below). |

Set them in the prod secret / overlay only. Leave unset in dev / CI.

## Exposure — internal only

The ingress (`k8s/base/ingress.yaml`) routes only `/api`, `/django-admin`,
`/static`, and `/` to the backend — **`/metrics` is not publicly routable.** It is
reachable only in-cluster via the `backend:8000` Service. Do **not** add an ingress
path for it. The `METRICS_TOKEN` bearer is an extra gate, not the primary boundary.

## Scraping (Prometheus, in-cluster)

Point a Prometheus job at the backend Service. Minimal static example:

```yaml
scrape_configs:
  - job_name: openshiksha-backend
    metrics_path: /metrics
    scheme: http
    static_configs:
      - targets: ["backend.openshiksha.svc.cluster.local:8000"]
    # If METRICS_TOKEN is set:
    authorization:
      type: Bearer
      credentials: "<METRICS_TOKEN>"
```

With the Prometheus Operator, prefer a `ServiceMonitor` selecting the `backend`
Service on the `http` port with `path: /metrics`.

### Single-process assumption

Prod runs a **single daphne ASGI process** (`CMD ["daphne", ...]` in
`backend/Dockerfile.prod`), so the default in-process registry is correct and **no
`PROMETHEUS_MULTIPROC_DIR`** is needed. If the server ever moves to a multi-worker
model (e.g. gunicorn with >1 worker), switch to prometheus_client multiprocess
mode — the counters would otherwise be per-worker and undercount. This is flagged
in `apps/core/metrics.py`.

## Metric catalogue

| Metric | Type | Labels | Meaning |
|--------|------|--------|---------|
| `openshiksha_build_info` | gauge | `version`, `git_sha`, `environment` | Always `1`; live build identity (matches `/api/v1/version/`). |
| `openshiksha_http_requests_total` | counter | `method`, `status_class` | HTTP requests handled (`status_class` = `2xx/3xx/4xx/5xx`). |
| `openshiksha_http_request_duration_seconds` | histogram | `method` | HTTP request latency. |
| `openshiksha_assignments_active` | gauge | — | Assignments open and not past due. |
| `openshiksha_submissions_pending_grading` | gauge | — | **Grade-queue depth** (submitted, ungraded). |
| `openshiksha_users` | gauge | `role` | User accounts by role. |
| `openshiksha_classrooms` / `openshiksha_subjectrooms` | gauge | — | Totals. |
| `openshiksha_celery_tasks` | gauge | `status` | Celery task counts by status (24h window). |
| `openshiksha_celery_oldest_pending_seconds` | gauge | — | Age of the oldest non-terminal Celery task (`0` when none). |
| `process_*`, `python_gc_*` | various | — | Runtime metrics from the prometheus_client default collectors. |

### MET-3 dependency: Celery result backend

The Celery gauges (`openshiksha_celery_*`) are derived **on-scrape** from the
`django_celery_results.TaskResult` table. That table is only populated when
`CELERY_RESULT_BACKEND` is the **database** backend (`django-db`). The default is
**Redis**, where the table stays empty — so the collector emits **nothing** there
(an honest no-op, not a misleading constant zero). To light these gauges up, set
`CELERY_RESULT_BACKEND=django-db`; until then the rest of the metrics are
unaffected.

## Grafana starter dashboard

Import `docs/ops/grafana/openshiksha-overview.json` (Grafana → Dashboards →
Import). It prompts for a Prometheus datasource (`DS_PROMETHEUS`) and renders:
request rate + p95 latency (MET-4), grade-queue depth + active assignments
(MET-2), Celery failures + oldest-pending age (MET-3), process RSS + build info
(MET-1). The datasource is templated, so no org-specific UID is committed.

## Quick local check

```bash
# Backend running with METRICS_ENABLED=true:
curl -s localhost:8000/metrics | grep openshiksha_
```
