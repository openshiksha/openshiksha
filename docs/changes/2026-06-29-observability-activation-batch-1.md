# Observability Activation — Batch 1 (OACT-1..5)

**Date:** 2026-06-29
**Initiative:** [Observability Activation](../initiatives/2026-observability-activation.md)
**Classification:** New / Improve / Infra + Docs

## Summary

The Production Observability initiative (closed 2026-06-28) built a complete
instrument panel — eight Prometheus alert rules, an Alertmanager config, a stdlib
ntfy bridge, a Grafana dashboard, a backup-freshness gauge — but **nobody plugged
it in**: `/metrics` emitted gauges nothing scraped, the rules sat in a YAML file
no Prometheus loaded, the dashboard JSON had no Grafana. This batch packages those
validated artifacts into a **deployable, CI-gated, operator-applied**
`k8s/monitoring/` stack and closes the one real code gap (the backup gauge prod
never populated).

## PRs

| # | PR | Class | What |
|:--:|---|---|---|
| OACT-1 | [#488](https://github.com/openshiksha/openshiksha/pull/488) | New / Infra | `k8s/monitoring/` Prometheus + CI kustomize/kubeconform gate |
| OACT-2 | [#489](https://github.com/openshiksha/openshiksha/pull/489) | New / Infra | Alertmanager + `alert_to_ntfy.py` sidecar; Prometheus→AM wiring |
| OACT-3 | [#490](https://github.com/openshiksha/openshiksha/pull/490) | New / Infra | Grafana provisioned with datasource + MET-5 dashboard |
| OACT-4 | [#491](https://github.com/openshiksha/openshiksha/pull/491) | Improve / Infra | Wire `record_backup_run` into the nightly backup CronJob |
| OACT-5 | _this_ | New / Docs | `docs/ops/monitoring-deploy.md` runbook + initiative/STATUS close-out |

## What changed and why

### The standalone-stack design (OACT-1..3)

`deploy-prod` runs `kubectl apply -k k8s/overlays/prod` on **every push to `qa`**.
Putting Prometheus/Alertmanager/Grafana in the prod overlay would auto-deploy a
resource-heavy stack onto the live single-node droplet with no operator opt-in. So
the stack lives in a standalone `k8s/monitoring/` kustomization the prod overlay
does **not** reference; the operator applies it deliberately with
`kubectl apply -k k8s/monitoring`. CI renders + `kubeconform -strict`-validates it
(extended `k8s-manifests` job) so manifest typos fail at PR time.

- **OACT-1**: Prometheus (`prom/prometheus:v2.54.1`, 7d `emptyDir` TSDB) scraping
  `backend:8000/metrics/` under job `openshiksha-backend` (the label the ALT-1
  `up{}` rule matches), with `METRICS_TOKEN` mounted as an optional credentials
  file. ALT-1 rules embedded verbatim as a ConfigMap (canonical source stays in
  `docs/ops/prometheus/`, still gated by `alerting-lint`).
- **OACT-2**: Alertmanager (`prom/alertmanager:v0.27.0`) + the `alert_to_ntfy.py`
  bridge as a `python:3.13-slim` sidecar. The backend image's build context is
  `./backend`, so the repo-root bridge script isn't in it — it's mounted verbatim
  from a ConfigMap (the script is stdlib-only, no pip install). Services
  `alertmanager:9093` + `alert-to-ntfy:9098` (the exact host the ALT-2 webhook
  config targets). Prometheus `alerting.alertmanagers` wired to it.
- **OACT-3**: Grafana (`grafana/grafana:11.2.0`) provisioned with the
  `prometheus:9090` datasource (default, fixed uid) and the verbatim MET-5
  dashboard; no ingress (port-forward only).

### Closing the backup-gauge gap (OACT-4)

`record_backup_run` and `openshiksha_backup_age_seconds` already existed and were
tested, but nothing called the command in prod (the backup image has no Django).
The prod backup pod is now two-phase: an **initContainer `backup`** runs the real
`pg_dump`→S3 and writes `/work/result.env` on success; a **main container
`record`** (backend image) sources it and runs `record_backup_run … || true`. The
`|| true` guarantees the record step can never fail the backup; a failed backup
fails the init phase (no record) and the `BackupStale`/`NeverRun` alerts cover it.
`pg_backup.sh` gained an opt-in `RESULT_FILE` write.

## Tests / validation

- `kubectl kustomize k8s/monitoring` renders (835 lines, 14 resources); every
  embedded ConfigMap payload validated — the bridge script **compiles** and
  `format_alert` matches the canonical, the dashboard parses as JSON (8 panels),
  all prometheus/alertmanager/grafana configs parse as YAML.
- `kubectl kustomize k8s/overlays/{qa,prod}` render; **qa byte-for-byte
  unchanged**; the prod CronJob now has `initContainers: [backup]` +
  `containers: [record]` + shared volume.
- `bash -n scripts/backup/pg_backup.sh` passes; `pytest test_metrics_backup.py` →
  5 passed (command/gauge unchanged).
- CI gates: extended `k8s-manifests` (kubeconform `-strict` on `k8s/monitoring`)
  + existing `alerting-lint` (promtool/amtool on the canonical rules/config).

## Migration notes

None — purely additive infra + docs. No DB migration. No secret committed
(`METRICS_TOKEN`/`ALERT_NTFY_URL`/`GRAFANA_ADMIN_PASSWORD` documented in
`secret.example.yaml`, provisioned out-of-band).

## Next steps

The only remaining step to the initiative's North Star is the **operator action**:
`kubectl apply -k k8s/monitoring` on the droplet (after confirming resource
headroom), provisioning the three secret keys, and setting `METRICS_ENABLED=true`.
See [`docs/ops/monitoring-deploy.md`](../ops/monitoring-deploy.md) for the
end-to-end "is it live?" checklist.
