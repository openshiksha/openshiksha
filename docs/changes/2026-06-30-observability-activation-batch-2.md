# Observability Activation — Batch 2 (durability & drift-safety)

**Date:** 2026-06-30
**Initiative:** [Observability Activation](../initiatives/2026-observability-activation.md)
**Classification:** Improve / New (infra + test + docs)

## Summary

Batch 1 (OACT-1..5) shipped the standalone `k8s/monitoring/` stack; two follow-up
commits then wired it live ([#493](https://github.com/openshiksha/openshiksha/pull/493)
exempted `/metrics/` from the HTTPS redirect, [#494](https://github.com/openshiksha/openshiksha/pull/494)
routed `openshiksha.org/grafana`). Batch 2 **hardens the now-live stack** on the
three axes a just-deployed monitoring stack fails on first — silent config drift,
data loss on pod restart, stale operator docs — plus gives the stack visibility
into its own liveness.

## PRs in this batch

| # | PR | What |
|:--:|---|---|
| OACT-6 | [#498](https://github.com/openshiksha/openshiksha/pull/498) | Manifest-vs-docs parity guard (pytest; drift fails CI). |
| OACT-7 | [#499](https://github.com/openshiksha/openshiksha/pull/499) | Reconcile stale Grafana access docs with the #494 ingress. |
| OACT-8 | [#500](https://github.com/openshiksha/openshiksha/pull/500) | Self-scrape prometheus + alertmanager + `MonitoringTargetDown`. |
| OACT-9 | [#501](https://github.com/openshiksha/openshiksha/pull/501) | Opt-in PVC-backed persistent-storage overlay. |
| OACT-11 | _this PR_ | Batch 2 ledger + STATUS update + this change doc. |

Each has its own change doc under `docs/changes/2026-06-30-oact{6,7,8,9}-*.md`.

## Why it matters

- **Drift-safety** — the two safety-critical embedded artifacts (ALT-1 rules,
  MET-5 dashboard) can no longer silently diverge from their `docs/ops/` sources;
  the parity test fails CI on any structural drift.
- **Restart-durability** — an operator who wants a week of trend data now applies
  one overlay (`k8s/monitoring-persistent`) and history survives pod restarts.
- **Self-observability** — the stack scrapes its own Prometheus + Alertmanager, so
  a degraded watcher produces an `up==0` signal instead of silence.
- **Honest docs** — the runbook and manifest header now match the real
  `openshiksha.org/grafana` access model instead of the pre-#494 "NO Ingress" claim.

## Learnings

- Kustomize forbids an overlay whose base is its **ancestor** directory — the
  persistent overlay is a sibling (`k8s/monitoring-persistent`) referencing
  `../monitoring`, not nested under it.
- This kustomize build (kubectl v1.34) does **not** honour the `$retainKeys`
  strategic-merge directive; swapping a volume's `emptyDir` for a PVC needs an
  explicit JSON6902 remove-then-add.

## Next steps

The initiative's last live step remains an **operator action**, not a PR:
`kubectl apply -k k8s/monitoring` (or `k8s/monitoring-persistent` for retention)
on the droplet + provisioning the `METRICS_TOKEN` / `ALERT_NTFY_URL` /
`GRAFANA_ADMIN_PASSWORD` secrets and `METRICS_ENABLED=true`. Once applied and
verified, the North Star is reached and the next planning run promotes a fresh top
initiative.
