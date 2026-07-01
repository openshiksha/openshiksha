# OACT-8 — Self-scrape the monitoring stack

**Date:** 2026-06-30
**Initiative:** Observability Activation (Batch 2 — durability & drift-safety)
**Classification:** Improve (infra)

## Summary

`prometheus.yml` had a single scrape job (`openshiksha-backend`). If Prometheus
couldn't reach Alertmanager, or Prometheus itself were degraded, there was no
`up{}` series for the monitoring stack's own components — so nothing could alert
on them. The watcher wasn't watched.

## What changed

- **`k8s/monitoring/prometheus.yaml`** — added two additive scrape jobs to the
  `prometheus-config` ConfigMap:
  - `prometheus` → `localhost:9090` (Prometheus's own `/metrics`)
  - `alertmanager` → `alertmanager:9093`
- **`docs/ops/prometheus/openshiksha-alerts.yml`** (canonical) + the
  `prometheus-rules` ConfigMap in `prometheus.yaml` (deployable copy) — added one
  alert rule, kept structurally identical (parity-guarded by OACT-6):
  - `MonitoringTargetDown`: `up{job=~"prometheus|alertmanager"} == 0`, `for: 10m`,
    `severity: warning`, summary "A monitoring-stack target is down".
  - `warning` (not critical): the app still serves while the monitoring stack
    cycles. `for: 10m` avoids flapping on a monitoring-stack rollout/restart.
- **`docs/ops/prometheus/openshiksha-alerts.test.yml`** — two promtool cases: an
  `alertmanager` target held down past `10m` fires the alert; a healthy
  `prometheus` target never fires.
- **`docs/ops/monitoring-deploy.md`** — the "is it live?" checklist now lists the
  two self-scrape targets and the 9th (`MonitoringTargetDown`) rule.

## Legacy reference

None — standard Prometheus self-monitoring.

## Tests

- `promtool check rules` / `promtool test rules` run in the existing
  `alerting-lint` CI job (promtool is not installed locally).
- Verified locally: the manifest `prometheus-rules` copy is **structurally equal**
  to the canonical source (the OACT-6 parity guard will enforce this once both
  merge); total rules = 9 with `MonitoringTargetDown` present; the three scrape
  jobs render; `kubectl kustomize k8s/monitoring` builds clean; both alert YAML
  and the test YAML parse.

## Migration notes

None — additive ConfigMap edits. The new targets only resolve once the stack is
applied in-cluster; `up==0` pre-apply is precisely the signal, gated `for: 10m`
to avoid boot-time flaps.

## Next steps

- OACT-9: opt-in persistent-storage overlay.
