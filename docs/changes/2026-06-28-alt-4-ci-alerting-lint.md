# ALT-4 — CI validation of the alerting artifacts

**Date:** 2026-06-28
**Initiative:** Production Observability & Operational Readiness — Batch 4 (Uptime & alerting)
**Classification:** Improve / Infra

## Summary

Adds an additive `alerting-lint` CI job to `.github/workflows/ci-cd.yaml` that
gates the Batch-4 alerting config-as-code the same way the existing
`k8s-manifests` job gates kustomize. The alert rules (ALT-1) and Alertmanager
config (ALT-2) reference **live metric names**; without a gate they rot the first
time a metric is renamed. This makes Batch 4 self-defending.

## The job

Pinned static binaries (no servers), mirroring the kubeconform gate's install
pattern:

1. `promtool check rules docs/ops/prometheus/openshiksha-alerts.yml` — schema/expr validity.
2. `promtool test rules docs/ops/prometheus/openshiksha-alerts.test.yml` — a new
   unit-test fixture asserting threshold + `for:` semantics:
   - `OpenShikshaBackupStale` **fires** at 37h, **not** at 1h.
   - `OpenShikshaGradeQueueBacklog` fires at 60 pending past its 30m window.
3. `amtool check-config docs/ops/alertmanager/alertmanager.yml` — Alertmanager config validity.
4. `pytest scripts/ops/tests/test_alert_to_ntfy.py` — the ALT-2 bridge formatter
   tests (the backend Test job only collects `backend/` tests, so the stdlib
   bridge's tests run here).

Pinned versions: Prometheus `2.53.1`, Alertmanager `0.27.0`.

## Validation (run locally before committing)

Downloaded the pinned promtool/amtool and ran the exact CI commands:

- `promtool check rules …` → **SUCCESS: 8 rules found**.
- `promtool test rules …` → **SUCCESS** (the `exp_annotations` were pinned to
  promtool's exact rendered text, incl. the `humanizeDuration` "1d 13h 0m 0s").
- `amtool check-config …` → **SUCCESS** (global + route + 1 receiver).
- `pytest scripts/ops/tests/test_alert_to_ntfy.py` → **7 passed**.
- Workflow YAML parses; `actionlint` runs in the existing `workflow-lint` job.

## Stacking note

This branch is stacked on ALT-1 + ALT-2 so the new job has real artifacts to
validate (a lint job with nothing to lint is meaningless). Once
[#481](https://github.com/openshiksha/openshiksha/pull/481) (ALT-1) and
[#482](https://github.com/openshiksha/openshiksha/pull/482) (ALT-2) merge, this
PR's diff reduces to just the CI job + the `.test.yml` fixture.

## Next steps

- ALT-5 documents the alert catalogue + Sentry routing and closes the initiative.
