# ALT-3 — Standalone in-cluster uptime probe CronJob

**Date:** 2026-06-28
**Initiative:** Production Observability & Operational Readiness — Batch 4 (Uptime & alerting)
**Classification:** New

## Summary

A floor-level "is the site up?" alarm that works with **zero Prometheus /
Alertmanager deployed** — the complement to the rule-based ALT-1/ALT-2 path:

- `scripts/ops/uptime_probe.sh` (`set -euo pipefail`) — curls the backend
  `/healthz/` + `/readyz/`; on **any** non-200 (or a connection failure → `000`)
  pushes a **single-line** DOWN alert to ntfy (`Title: OpenShiksha DOWN`, high
  priority, `rotating_light`) naming the failing endpoint + status code, and exits
  non-zero so the Job is marked failed. Success path is **silent** (no per-run
  spam). The ntfy URL is read from env and **never echoed**.
- `k8s/overlays/prod/uptime-probe-cronjob.yaml` — `batch/v1 CronJob`,
  `schedule: "*/5 * * * *"`, `concurrencyPolicy: Forbid`,
  `successful/failedJobsHistoryLimit: 3`, `backoffLimit: 1`,
  `restartPolicy: OnFailure`. **Prod-overlay-only** (referenced only from
  `k8s/overlays/prod/kustomization.yaml`, same pattern as `backup-cronjob.yaml`).

## Image decision

Reuses the **already-published BAK-1 backup image**
(`ghcr.io/openshiksha/openshiksha-backup:prod`, `postgres:15-alpine` base) which
already has `curl` + `bash` + `ca-certificates` — **no new CI publish target**.
The probe script is added to that image (`backend/Dockerfile.backup` COPY) and the
CronJob overrides the backup ENTRYPOINT with
`command: ["/usr/local/bin/uptime_probe.sh"]`. The image rebuilds + republishes on
the existing `build-publish` matrix (context is the repo root, so `scripts/ops/`
is in scope).

## Config / secrets

- `PROBE_BASE_URL` — **non-secret** ConfigMap value (`http://backend:8000`,
  in-cluster Service DNS), added to `k8s/overlays/prod/configmap-patch.yaml`.
- `ALERT_NTFY_URL` — secret (ntfy topic URL), added empty to
  `k8s/base/secret.example.yaml` with a comment (shared with the ALT-2 bridge).

## Validation

- `bash -n scripts/ops/uptime_probe.sh` clean. (shellcheck runs in dev/CI; not
  installed on this box — the parse check + functional tests below cover it.)
- **Functional test** against a local stub server:
  - `/readyz/` → 503 ⇒ exit **1**, logs the failing endpoint, attempts push
    (no URL set ⇒ safe "cannot push" warning, never crashes).
  - both 200 ⇒ exit **0**, **silent** stderr (success path).
- `kubectl kustomize k8s/overlays/prod` includes the CronJob + `PROBE_BASE_URL`;
  `kubectl kustomize k8s/overlays/qa` is **byte-for-byte unchanged** (diff: empty).
- `kubeconform -strict` runs in the existing k8s-manifests CI gate (#459).

## Trade-off (documented for ALT-5)

A transient blip can page every 5 min (acceptable for a floor probe). The
rule-based ALT-1 path debounces with `for:` windows; the standalone probe
deliberately does not, trading a little noise for working with no monitoring stack
at all.

## Next steps

- ALT-4 adds the `alerting-lint` CI gate (promtool/amtool + the ALT-2 pytest).
- ALT-5 documents how the probe fits the overall alerting story.
