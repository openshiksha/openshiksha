# Observability Activation

**Status:** Active (promoted 2026-06-29)
**Lane:** plan/execute (foundation-hardening — **not** AI-Native; the
`ai-features` routine fence is respected)
**Predecessor:** [Production Observability & Operational Readiness](2026-production-observability.md)
(Done 2026-06-28)

## North Star

The validated observability artifacts the prior initiative produced **run live on
the droplet with one `kubectl apply`**, and the backup-freshness gauge reads real
data — i.e. the instrument panel is plugged in, not just built.

## Why this exists

Production Observability shipped four batches (OBS / MET / BAK / ALT) and reached
its North Star — but its own close-out is honest that the spine is **validated,
not live**:

> *"Prometheus + Alertmanager are not yet deployed in `k8s/` — ALT-1/2/4 are
> validated drop-in artifacts; the ALT-3 probe is the only piece that alerts with
> zero stack."*

So today: `/metrics` emits gauges nothing scrapes; eight alert rules sit in a YAML
file no Prometheus loads; a Grafana dashboard JSON has no Grafana to render it.
The close-out named three operational follow-ups — this initiative delivers the
two that are code:

1. **Deploy Prometheus + Alertmanager so ALT-1/2/4 go live.** → OACT-1/2.
2. **Wire `record_backup_run` so prod populates `openshiksha_backup_age_seconds`.**
   → OACT-4.
3. ~~Wire `VITE_SENTRY_DSN` into the CI frontend build~~ — **already done**
   (`ci-cd.yaml:530`); only an out-of-band DSN secret is pending (operational).

Plus the dashboard that makes the metrics legible (OACT-3) and the runbook that
makes the whole thing repeatable (OACT-5).

## Design constraint — additive, operator-applied, never auto-deployed

`deploy-prod` runs `kubectl apply -k k8s/overlays/prod` on **every push to `qa`**
(`ci-cd.yaml:618`). Putting the monitoring stack in the prod overlay would
**auto-deploy** Prometheus + Alertmanager + Grafana onto the live single-node
droplet on merge, with no operator opt-in. So the stack lives in a **standalone
`k8s/monitoring/` kustomization the prod overlay does not reference**. The PRs add
only **CI-gated artifacts** (kustomize + kubeconform `-strict`); the operator runs
`kubectl apply -k k8s/monitoring` deliberately, when the droplet has headroom.
This extends the prior initiative's "drop-in artifact" philosophy one step closer
to live without forcing a heavy prod change through a routine PR.

## Batch 1 — OACT-1..5 (planned 2026-06-29)

See [`../daily-plans/2026-06-29-plan.md`](../daily-plans/2026-06-29-plan.md) for
the full build spec.

| # | Item | Class | Depends on |
|:--:|---|---|---|
| OACT-1 | Prometheus manifest in `k8s/monitoring/` + CI kustomize/kubeconform gate | New / Infra | — (build first) |
| OACT-2 | Alertmanager manifest + `alert_to_ntfy.py` sidecar; Prometheus→AM wiring | New / Infra | OACT-1 |
| OACT-3 | Grafana manifest provisioned with Prometheus datasource + MET-5 dashboard | New / Infra | OACT-1 |
| OACT-4 | Wire `record_backup_run` into the nightly backup CronJob (prod overlay) | Improve / Infra | — (independent; auto-deploys) |
| OACT-5 | `docs/ops/monitoring-deploy.md` runbook + this doc + STATUS close-out | New / Docs | — (last) |

**Build order:** OACT-1 → OACT-2 → OACT-3 → OACT-4 → OACT-5. Floor-value subset if
time is short: **OACT-1 + OACT-4 + OACT-5**.

## Definition of Done

- [ ] `k8s/monitoring/` renders and passes kubeconform `-strict` in CI.
- [ ] Prometheus scrapes the backend `/metrics` (with `METRICS_TOKEN`) and loads
      the ALT-1 alert rules.
- [ ] Alertmanager routes firing alerts through the `alert_to_ntfy` bridge to ntfy.
- [ ] Grafana auto-provisions the Prometheus datasource and the overview dashboard.
- [ ] The nightly backup CronJob writes a `BackupRun` row so
      `openshiksha_backup_age_seconds` reads real data in prod.
- [ ] `docs/ops/monitoring-deploy.md` lets an operator apply + verify the stack
      end-to-end.
- [ ] qa/dev kustomize output is byte-for-byte unchanged; no secret committed.

## Out of scope / follow-ups

- The actual `kubectl apply -k k8s/monitoring` on the droplet is an **operator
  action** (resource headroom call), not a CI step.
- Provisioning `VITE_SENTRY_DSN`, `METRICS_TOKEN`, `ALERT_NTFY_URL`,
  `GRAFANA_ADMIN_PASSWORD` into `openshiksha-secrets` is operational.
- Persistent (PVC-backed) Prometheus TSDB / Grafana state is deferred — the
  manifests use `emptyDir` to stay light on the single droplet; an operator who
  wants retention across pod restarts swaps in a PVC.
