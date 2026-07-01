# OACT-6 — Manifest-vs-docs parity guard

**Date:** 2026-06-30
**Initiative:** Observability Activation (Batch 2 — durability & drift-safety)
**Classification:** New (test / CI guard)

## Summary

The deployable `k8s/monitoring/` manifests embed two safety-critical artifacts
**verbatim**, each a hand-maintained copy of a canonical source under `docs/ops/`:

- `k8s/monitoring/prometheus.yaml` → ConfigMap `prometheus-rules` embeds
  `docs/ops/prometheus/openshiksha-alerts.yml` (the ALT-1 alert rules).
- `k8s/monitoring/grafana.yaml` → ConfigMap `grafana-dashboard-overview` embeds
  `docs/ops/grafana/openshiksha-overview.json` (the MET-5 dashboard).

Until now the only thing keeping them in sync was a "keep the two in sync"
comment. Editing the `docs/` copy while forgetting the manifest (or vice versa)
leaves `alerting-lint` green — it lints the `docs/` source — while the
**deployed** alarm is stale. That is the classic observability failure: the alert
you think you changed didn't change.

This adds a pytest that fails CI on any such drift.

## What changed

- New `backend/openshiksha/apps/core/tests/test_monitoring_manifest_parity.py`:
  - `test_alert_rules_embed_matches_canonical_source` — parses the embedded
    `prometheus-rules` ConfigMap data and the canonical YAML, asserts structural
    equality.
  - `test_dashboard_embed_matches_canonical_source` — same shape for the Grafana
    dashboard JSON.
  - `test_embedded_copies_are_non_empty_and_parse` — a truncated paste fails
    loudly (`groups` / `panels` must be present).

## Why parsed structure, not byte match

The block-scalar embed reflows indentation and quoting, so a raw byte compare
would be brittle and produce false failures. Comparing `yaml.safe_load` /
`json.loads` output tolerates cosmetic reformatting while still catching any real
content drift (a changed threshold, a renamed alert, a dropped panel).

## Tests

- 3 tests, all passing.
- Prove-it-fails: temporarily changed a threshold in the manifest ConfigMap
  (`> 129600` → `> 999999`); the rules-parity test went red with the actionable
  "re-copy the canonical rules" message; reverted and it passed again.

## Migration notes

None — pure file-parsing test, no DB, no models, no manifest changes.

## Next steps

- OACT-8 will add a `MonitoringTargetDown` rule to the canonical source and
  re-copy it into the manifest; this guard now enforces that re-copy.
