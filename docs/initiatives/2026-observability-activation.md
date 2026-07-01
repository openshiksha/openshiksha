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

### Shipped 2026-06-29

| # | PR | Notes |
|:--:|---|---|
| OACT-1 | [#488](https://github.com/openshiksha/openshiksha/pull/488) | `k8s/monitoring/` Prometheus (scrape `backend:8000/metrics/` job `openshiksha-backend` + verbatim ALT-1 rules) + CI kustomize/kubeconform gate; `METRICS_TOKEN`/`GRAFANA_ADMIN_PASSWORD` documented in `secret.example`. |
| OACT-2 | [#489](https://github.com/openshiksha/openshiksha/pull/489) | Alertmanager (verbatim ALT-2 config) + `alert_to_ntfy.py` as a `python:3.13-slim` ConfigMap-mounted sidecar; Prometheus `alerting.alertmanagers` → `alertmanager:9093`. Stacked on #488. |
| OACT-3 | [#490](https://github.com/openshiksha/openshiksha/pull/490) | Grafana provisioned with the `prometheus:9090` datasource (default) + verbatim MET-5 dashboard; no ingress (port-forward). Stacked on #489. |
| OACT-4 | [#491](https://github.com/openshiksha/openshiksha/pull/491) | Two-phase prod backup pod: init `backup` writes `/work/result.env`, main `record` runs `record_backup_run … \|\| true`. Populates `openshiksha_backup_age_seconds`. Independent (auto-deploys). |
| OACT-5 | _this PR_ | `docs/ops/monitoring-deploy.md` runbook + this ledger + STATUS close-out. |

### Live-wiring follow-ups (post-Batch-1)

After the Batch 1 close-out, the stack stopped being a drawer artifact and started
being plugged into the live cluster:

| # | PR | Notes |
|:--:|---|---|
| — | [#493](https://github.com/openshiksha/openshiksha/pull/493) | Exempt `/metrics/` from the HTTPS redirect so Prometheus can scrape it. |
| — | [#494](https://github.com/openshiksha/openshiksha/pull/494) | Route `openshiksha.org/grafana` → the Grafana Service (login-gated sub-path). |

### Batch 2 — durability & drift-safety (Shipped 2026-06-30)

Hardening the now-live stack on the three axes a just-deployed monitoring stack
fails on first — silent config drift, data loss on pod restart, and stale operator
docs — plus giving the stack visibility into its own liveness.

| # | PR | Notes |
|:--:|---|---|
| OACT-6 | [#498](https://github.com/openshiksha/openshiksha/pull/498) | Manifest-vs-docs **parity guard**: pytest asserts the ALT-1 rules and MET-5 dashboard embedded in the manifests match their canonical `docs/ops/` sources by parsed structure; drift fails CI. Closes the "keep the two in sync" comment-only gap. |
| OACT-7 | [#499](https://github.com/openshiksha/openshiksha/pull/499) | Reconcile the stale Grafana access docs: `grafana.yaml` header + `monitoring-deploy.md` now describe the real `openshiksha.org/grafana` sub-path access (#494) with the 503-until-`k8s/monitoring`-applied ordering; port-forward demoted to fallback. |
| OACT-8 | [#500](https://github.com/openshiksha/openshiksha/pull/500) | **Self-scrape** the stack: `prometheus` + `alertmanager` scrape jobs + a `MonitoringTargetDown` rule (`up{job=~"prometheus\|alertmanager"}==0`, `for 10m`, warning) in the canonical source, re-copied to the manifest (parity-guarded by OACT-6). Closes the "who watches the watcher" gap. |
| OACT-9 | [#501](https://github.com/openshiksha/openshiksha/pull/501) | Opt-in **persistent-storage overlay** `k8s/monitoring-persistent/`: swaps the Prometheus TSDB + Grafana `emptyDir` volumes to PVCs (JSON6902 patches) so history survives pod restarts; base stays light. Both variants CI-gated. |
| OACT-11 | _this PR_ | Batch 2 ledger + STATUS update + change doc. |

**Learnings:**
- Kustomize forbids an overlay whose base is its **ancestor** directory ("cycle
  detected") — the persistent overlay had to be a sibling (`k8s/monitoring-persistent`)
  referencing `../monitoring`, not nested under it.
- This kustomize build (kubectl v1.34) does **not** honour the `$retainKeys`
  strategic-merge directive (it leaves the directive key + both volume sources in
  the output). Replacing a volume's `emptyDir` with a PVC needs an explicit
  JSON6902 remove-then-add.
- The parity guard compares **parsed** structure, not bytes — tolerating the
  block-scalar embed's reflow while still catching real content drift.

## Definition of Done

- [x] `k8s/monitoring/` renders and passes kubeconform `-strict` in CI.
- [x] Prometheus scrapes the backend `/metrics` (with `METRICS_TOKEN`) and loads
      the ALT-1 alert rules. _(manifest validated; live scrape is the operator apply)_
- [x] Alertmanager routes firing alerts through the `alert_to_ntfy` bridge to ntfy.
- [x] Grafana auto-provisions the Prometheus datasource and the overview dashboard.
- [x] The nightly backup CronJob writes a `BackupRun` row so
      `openshiksha_backup_age_seconds` reads real data in prod.
- [x] `docs/ops/monitoring-deploy.md` lets an operator apply + verify the stack
      end-to-end.
- [x] qa/dev kustomize output is byte-for-byte unchanged; no secret committed.

**Batch 1 (OACT-1..5) complete.** All artifacts shipped + CI-gated; the remaining
step — `kubectl apply -k k8s/monitoring` on the droplet — is the documented
**operator action** (resource-headroom call), not a CI/routine step.

## Out of scope / follow-ups

- The actual `kubectl apply -k k8s/monitoring` on the droplet is an **operator
  action** (resource headroom call), not a CI step.
- Provisioning `VITE_SENTRY_DSN`, `METRICS_TOKEN`, `ALERT_NTFY_URL`,
  `GRAFANA_ADMIN_PASSWORD` into `openshiksha-secrets` is operational.
- ~~Persistent (PVC-backed) Prometheus TSDB / Grafana state is deferred.~~
  **Delivered in Batch 2 (OACT-9, [#501](https://github.com/openshiksha/openshiksha/pull/501)):**
  the base still uses `emptyDir` to stay light; an operator who wants retention
  across pod restarts applies the opt-in `k8s/monitoring-persistent` overlay
  instead of the base.
