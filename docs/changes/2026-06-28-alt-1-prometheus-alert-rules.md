# ALT-1 — Prometheus alerting-rules artifact

**Date:** 2026-06-28
**Initiative:** Production Observability & Operational Readiness — Batch 4 (Uptime & alerting)
**Classification:** New / Docs

## Summary

Adds `docs/ops/prometheus/openshiksha-alerts.yml`, a drop-in Prometheus rule file
that expresses the alerts predicting (or announcing) an OpenShiksha incident,
written **entirely against metrics the platform already emits**. It is the
alerting sibling of the Batch-3 Grafana starter — an artifact an operator points
`rule_files:` at, not a live deployment. Pure addition; touches no running code,
no manifests, no dev/CI/qa behaviour.

## Alerts (8 total)

| Alert | Expr (metric) | Threshold | `for` | Severity |
|---|---|---|---|---|
| `OpenShikshaBackupStale` | `openshiksha_backup_age_seconds` | > 36h | 10m | critical |
| `OpenShikshaBackupNeverRun` | `openshiksha_backup_last_success_timestamp == 0` / `absent(...)` | — | 6h | critical |
| `OpenShikshaGradeQueueBacklog` | `openshiksha_submissions_pending_grading` | > 50 | 30m | warning |
| `OpenShikshaCeleryOldestPending` | `openshiksha_celery_oldest_pending_seconds` | > 15m | 15m | warning |
| `OpenShikshaCeleryFailureRate` | `openshiksha_celery_tasks{status="FAILURE"}` / total | > 10% | 15m | warning |
| `OpenShikshaHighHTTPErrorRate` | `openshiksha_http_requests_total{status_class="5xx"}` ratio | > 5% | 10m | critical |
| `OpenShikshaHighLatencyP95` | `histogram_quantile(0.95, openshiksha_http_request_duration_seconds_bucket)` | > 1.5s | 10m | warning |
| `OpenShikshaTargetDown` | `up{job="openshiksha-backend"} == 0` | — | 5m | critical |

## Metric-name cross-check

Every metric/label name was verified against
`backend/openshiksha/apps/core/metrics.py`:

- `openshiksha_backup_age_seconds`, `openshiksha_backup_last_success_timestamp` —
  `BusinessMetricsCollector` (BAK-4). The age gauge is **deliberately absent**
  until a first successful backup exists; `OpenShikshaBackupNeverRun` covers that
  cold/total-outage case via the always-emitted timestamp gauge + `absent()`.
- `openshiksha_submissions_pending_grading` — `BusinessMetricsCollector` (MET-2).
- `openshiksha_celery_tasks{status}`, `openshiksha_celery_oldest_pending_seconds` —
  `TaskMetricsCollector` (MET-3). Both only carry data under the **django-db**
  result backend; under the default Redis backend they are an honest no-op and the
  two Celery alerts simply never fire (documented inline + in the runbook).
- `openshiksha_http_requests_total` — the MET-4 Counter is declared as
  `openshiksha_http_requests`; prometheus_client appends `_total` to the exposed
  series. Labelled by `status_class` (2xx/3xx/4xx/5xx), never raw path.
- `openshiksha_http_request_duration_seconds_bucket` — the MET-4 Histogram's
  bucket series, summed per-`le` before `histogram_quantile`.
- `up{job="openshiksha-backend"}` — Prometheus' synthetic scrape-health series;
  the job label is operator-defined and documented as adjustable.

## Design notes

- Thresholds are conservative **starting points**, same "operator tunes" framing
  as the Grafana starter and the BAK backup-age threshold — spelled out in the
  ALT-5 runbook (`docs/ops/alerting.md`).
- Ratio exprs use `clamp_min(denominator, …)` so an empty series yields no result
  rather than a divide-by-zero / NaN page.

## Validation

- `python` YAML-structure check: every rule has `alert`/`expr`/`labels.severity`/
  `annotations.summary`+`description` (8 alerts across 4 groups). ✅
- `promtool check rules` runs in CI via the ALT-4 `alerting-lint` job (promtool is
  not installed on this dev box; the CI gate is the authoritative check).

## Next steps

- ALT-2 routes these alerts (Alertmanager config + ntfy bridge).
- ALT-4 adds the `promtool check rules` CI gate so the file cannot silently rot.
- ALT-5 documents the alert catalogue + first-response actions.
