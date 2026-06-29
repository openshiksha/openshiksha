#!/usr/bin/env bash
#
# uptime_probe.sh — dependency-free in-cluster uptime probe (Production
# Observability Batch 4, ALT-3).
#
# Curls the backend liveness (`/healthz/`) and readiness (`/readyz/`) endpoints
# and, on ANY non-200 (or a curl/connection failure), pushes a single-line alert
# to ntfy and exits non-zero so the owning Kubernetes Job is marked failed (which
# also surfaces in the Batch-2 Celery/Job visibility). The success path is SILENT
# (no per-run spam). This is the floor-level "is the site up?" alarm — it works
# with ZERO Prometheus / Alertmanager deployed, complementing the rule-based
# ALT-1/ALT-2 path.
#
# Packaged into the BAK-1 backup image (which already has bash + curl +
# ca-certificates) and run by k8s/overlays/prod/uptime-probe-cronjob.yaml every
# 5 minutes. Prod-overlay-only, so qa/dev kustomize output is unchanged.
#
# Configuration (all via environment — the ntfy URL is a write capability and is
# NEVER echoed):
#   PROBE_BASE_URL   in-cluster base URL of the backend, e.g. http://backend:8000
#                    (non-secret; a ConfigMap value).
#   ALERT_NTFY_URL   ntfy topic URL to push DOWN alerts to (secret; server-side).
#                    If unset, the probe still checks + exits non-zero on failure,
#                    but cannot push (a warning is logged without the URL).
set -euo pipefail

BASE_URL="${PROBE_BASE_URL:-http://backend:8000}"

# Push a single-line DOWN alert to ntfy. Never echoes ALERT_NTFY_URL.
notify_down() {
    msg="$1"
    if [ -z "${ALERT_NTFY_URL:-}" ]; then
        echo "uptime_probe: ALERT_NTFY_URL unset; cannot push alert" >&2
        return 0
    fi
    curl --silent --show-error --max-time 10 \
        -H "Title: OpenShiksha DOWN" \
        -H "Priority: high" \
        -H "Tags: rotating_light" \
        -d "$msg" \
        "$ALERT_NTFY_URL" >/dev/null 2>&1 || \
        echo "uptime_probe: failed to push ntfy alert" >&2
}

# Probe one endpoint; echo its HTTP status (000 on connection failure). The probe
# itself must not abort on a curl non-zero, so the call is guarded.
probe() {
    path="$1"
    curl --silent --output /dev/null --max-time 10 \
        --write-out "%{http_code}" "${BASE_URL}${path}" 2>/dev/null || echo "000"
}

failures=""
for path in "/healthz/" "/readyz/"; do
    code="$(probe "$path")"
    if [ "$code" != "200" ]; then
        echo "uptime_probe: ${path} returned ${code}" >&2
        failures="${failures} ${path}=${code}"
    fi
done

if [ -n "$failures" ]; then
    notify_down "Backend health check failed:${failures} (base ${BASE_URL})"
    exit 1
fi

echo "uptime_probe: OK (healthz + readyz 200)"
exit 0
