# OACT-9 — Opt-in persistent-storage overlay for the monitoring stack

**Date:** 2026-06-30
**Initiative:** Observability Activation (Batch 2 — durability & drift-safety)
**Classification:** Improve (infra)

## Summary

The base `k8s/monitoring` uses `emptyDir` for both the Prometheus TSDB and
Grafana's state. With the base's `strategy: Recreate`, every pod restart (node
reboot, image bump, `kubectl rollout`) wipes all metrics history and Grafana
state — a data-loss trap once an operator relies on trend data. This adds a
ready-to-apply overlay that swaps both volumes to PersistentVolumeClaims, while
the base stays light.

## What changed

- New `k8s/monitoring-persistent/`:
  - `pvcs.yaml` — `prometheus-tsdb` (8Gi) and `grafana-data` (2Gi), both
    `ReadWriteOnce`, no `storageClassName` (k3s `local-path` binds them; a non-k3s
    operator sets a class).
  - `patch-prometheus-tsdb.yaml` / `patch-grafana-data.yaml` — JSON6902 patches
    that remove each volume's `emptyDir` source and add a `persistentVolumeClaim`.
  - `kustomization.yaml` — `resources: ../monitoring` + the PVCs, plus the two
    patches. Apply with `kubectl apply -k k8s/monitoring-persistent` **instead of**
    the base.
- `.github/workflows/ci-cd.yaml` — the monitoring validation step now renders +
  kubeconform-validates **both** `k8s/monitoring` and `k8s/monitoring-persistent`
  on every PR.
- `docs/ops/monitoring-deploy.md` — new "Ephemeral vs persistent storage" section
  (when to pick which, the storageClass note).

## Design decisions & gotchas

- **Sibling dir, not nested.** The plan named `k8s/monitoring/overlays/persistent`,
  but kustomize forbids an overlay whose base is its own **ancestor** directory
  ("cycle detected"), and the base must stay applyable as
  `kubectl apply -k k8s/monitoring`. So the overlay is a sibling
  (`k8s/monitoring-persistent`) referencing `../monitoring` — no base resource-list
  duplication, no drift hazard.
- **JSON6902, not `$retainKeys`.** A strategic-merge patch can only *add*
  `persistentVolumeClaim`, leaving `emptyDir` in place (a Volume may set only one
  source), and this kustomize build (kubectl v1.34) does not honour the
  `$retainKeys` directive — it left the directive key literally in the output and
  kept both sources. The JSON6902 remove-then-add is explicit and renders a clean
  single-source volume.

## Tests

- `kubectl kustomize k8s/monitoring-persistent` renders; verified both target
  volumes end up with **only** `persistentVolumeClaim` (no residual `emptyDir`),
  the two PVCs are namespaced `openshiksha-prod` at 8Gi/2Gi, and the base still
  renders `emptyDir` (unchanged).
- kubeconform (`-strict`) runs in the extended CI monitoring step (not installed
  locally).

## Migration notes

None — additive, opt-in. The base default is untouched; operators choose the
overlay only when they want retention.

## Next steps

- OACT-11: Batch 2 close-out (ledger + STATUS + change doc index).
