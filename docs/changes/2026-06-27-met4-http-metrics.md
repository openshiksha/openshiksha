# MET-4 — Gated HTTP request-metrics middleware

**Date:** 2026-06-27
**Initiative:** [Production Observability & Operational Readiness](../initiatives/2026-production-observability.md) — Batch 2, increment 4 of 5
**Plan:** [2026-06-27-plan.md](../daily-plans/2026-06-27-plan.md)
**Classification:** New

## Summary

Adds `MetricsMiddleware`, which records HTTP request count + latency into
Prometheus **only when `METRICS_ENABLED`**. When disabled it is a pure
pass-through — no metric object is touched, no measurable overhead — so default
behaviour is byte-for-byte today's. Placed in `MIDDLEWARE` immediately after
`RequestIDMiddleware` so the request-id context is already set.

## Metrics

| Metric | Type | Labels | Meaning |
|--------|------|--------|---------|
| `openshiksha_http_requests_total` | Counter | `method`, `status_class` | Requests handled |
| `openshiksha_http_request_duration_seconds` | Histogram | `method` | Request latency |

`status_class` is `2xx/3xx/4xx/5xx` — **not** raw path — to avoid unbounded
cardinality from per-id URLs. The Counter/Histogram are **module-level singletons**
defined once at import (in `apps/core/metrics.py`) so they're never recreated per
request (which would raise a "Duplicated timeseries" registry error).

## Operability bar

1. **Additive & env-gated** — pure pass-through when `METRICS_ENABLED` is off
   (`test_pure_passthrough_records_nothing`).
2. **Probe-safe** — no probe paths touched.
3. **No secrets** — only method + status class + timing, never path/body/PII.
4. **No perf/offline regression** — backend-only; disabled path does one boolean
   check per request.
5. **Tested both ways** — enabled (counter increments + latency observed +
   exposed on `/metrics`) and disabled (no counter movement).

## Tests

`backend/openshiksha/apps/core/tests/test_metrics_http.py` (3 tests): a request
through the stack increments `openshiksha_http_requests_total` and observes a
duration sample; the families appear in the `/metrics` exposition; and with
metrics disabled the middleware calls downstream but records nothing.

## Migration notes

None — no model changes. `MetricsMiddleware` is added to `MIDDLEWARE` but is inert
unless `METRICS_ENABLED=true`.

## Next steps

- **MET-5** — Grafana starter dashboard + scrape runbook + STATUS/ledger update
  (marks Batch 2 shipped).
