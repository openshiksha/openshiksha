# OACT-7 — Reconcile stale Grafana access docs

**Date:** 2026-06-30
**Initiative:** Observability Activation (Batch 2 — durability & drift-safety)
**Classification:** Docs (reconciliation)

## Summary

`#494` gave Grafana a real public ingress route (`openshiksha.org/grafana`,
login-gated, served from a sub-path), but two operator-facing docs still claimed
the opposite — "NO Ingress — reach it via port-forward". An operator reading them
would port-forward and never discover the public sub-path. Stale ops docs during
a live bring-up are how mistakes happen.

## What changed

- **`k8s/monitoring/grafana.yaml` header** — replaced the "NO Ingress / keep it
  off the public internet" block with the real access model: primary access is
  the login-gated `openshiksha.org/grafana` sub-path via the prod-overlay ingress
  (`k8s/overlays/prod/ingress-patch.yaml`); port-forward is now the **fallback**.
  Mirrors the ingress patch's own caveat that the `grafana` Service only exists
  once `k8s/monitoring` is applied, so `/grafana` 503s until then.
- **`docs/ops/monitoring-deploy.md`** — the "Grafana shows data" verification step
  now leads with the sub-path URL + `GRAFANA_ADMIN_PASSWORD` login and spells out
  the 503-until-applied ordering between the auto-deploying ingress route and the
  operator-applied Service; port-forward retained as the fallback path.

## Legacy reference

None — doc reconciliation of net-new modern infra.

## Tests

No code. Read-back + grep confirm no stale primary-access claim remains
("NO Ingress" / "off the public internet" / "no public ingress" all gone;
`port-forward svc/grafana` appears only as the fallback). The OACT-6 parity guard
is unaffected — only the manifest's leading comment changed, not the embedded
ConfigMap data.

## Next steps

None for this item.
