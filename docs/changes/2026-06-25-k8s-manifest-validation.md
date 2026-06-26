# 2026-06-25 — K8s manifest validation gate (kustomize + kubeconform)

**Classification:** CI / infrastructure (new static gate; no runtime behaviour
change).

## Summary
Added a `k8s-manifests` job to [`ci-cd.yaml`](../../.github/workflows/ci-cd.yaml)
that renders every kustomize overlay (`k8s/overlays/qa`, `k8s/overlays/prod` —
base is pulled in transitively) and validates the rendered output against the
upstream Kubernetes JSON schemas with [`kubeconform`](https://github.com/yannh/kubeconform)
in `-strict` mode. The job is wired into `build-publish`'s `needs:`, so invalid
manifests now block the image build and the deploy that follows.

## Why
Until now nothing validated the k8s manifests on a PR. The only `kustomize build`
calls live **inside** the `deploy-qa` / `deploy-prod` jobs — they run on the
cluster, *after* the image build, and only on the `qa` / `prod` branches. So a
typo in a manifest (a mis-spelled field, a malformed probe block, a bad type)
sailed through CI green and only surfaced at `kubectl apply` / rollout against the
**live** environment.

This is timely: the in-flight **Production Observability** initiative
([`OBS-1`](../initiatives/2026-production-observability.md)) repoints the backend
`readinessProbe` in [`k8s/base/backend.yaml`](../../k8s/base/backend.yaml) — a
hand-edited probe block is exactly the kind of change a schema gate catches before
it can break a rollout.

## Why `-strict`
Plain kubeconform validation allows unknown/additional properties, so a typo'd key
(e.g. `htpGet:` instead of `httpGet:` in a probe) passes silently. `-strict`
rejects unknown fields, catching that whole class of bug. Verified locally:

- Both overlays render (13 resources each) and pass `kubeconform -strict`.
- A negative test injecting `htpGet` into the probe fails the gate under
  `-strict` (`additionalProperties 'htpGet' not allowed`) while passing under
  non-strict — confirming the gate has teeth.

## Pinning notes
- `kubectl` is installed via `azure/setup-kubectl@v5` at `v1.31.0` — the same
  action and version the deploy jobs use, so the PR-time renderer matches the
  one that applies manifests to the cluster.
- `-kubernetes-version 1.31.0` targets the same API surface.
- `kubeconform` is pinned to `v0.6.7`.
- `-ignore-missing-schemas` keeps the gate from failing on any future CRD-backed
  resource whose schema isn't in the default store (none today).
