# Monitoring stack deployment runbook (Observability Activation, OACT-5)

How to deploy and verify the standalone `k8s/monitoring/` stack — Prometheus →
Alertmanager (+ ntfy bridge) → Grafana — on the production droplet. This is the
runbook that makes the [Observability Activation](../initiatives/2026-observability-activation.md)
initiative's North Star reachable: *the validated artifacts run live with one
apply.*

> **Why a separate apply?** `deploy-prod` runs `kubectl apply -k
> k8s/overlays/prod` on every push to `qa`. The monitoring stack lives in a
> standalone `k8s/monitoring/` kustomization the prod overlay does **not**
> reference, so it never auto-deploys onto the live single-node droplet. You apply
> it **deliberately**, when the droplet has headroom.

## What gets deployed

`kubectl apply -k k8s/monitoring` creates, in namespace `openshiksha-prod`:

| Component | Image | Service | Purpose |
|---|---|---|---|
| Prometheus | `prom/prometheus:v2.54.1` | `prometheus:9090` | Scrapes backend `/metrics/`, loads the ALT-1 alert rules |
| Alertmanager | `prom/alertmanager:v0.27.0` | `alertmanager:9093` | Routes firing alerts |
| ntfy bridge (sidecar) | `python:3.13-slim` | `alert-to-ntfy:9098` | Translates Alertmanager webhooks → ntfy pushes |
| Grafana | `grafana/grafana:11.2.0` | `grafana:3000` | Dashboards (Prometheus datasource + MET-5 overview) |

**Resource footprint** (requests across the four containers): ~**0.21 vCPU** /
~**0.47 GiB** memory requested (limits ~1.05 vCPU / ~0.94 GiB). **Confirm the
droplet has headroom before applying.**

### Ephemeral vs persistent storage

The base `k8s/monitoring` uses `emptyDir` for both the Prometheus TSDB and
Grafana's state — light, but a pod restart (node reboot, image bump,
`kubectl rollout`) **wipes all metrics history and Grafana state**. Fine for a
first-light apply; a data-loss trap once you rely on a week of trend data.

For retention across restarts, apply the **opt-in persistent overlay instead of
the base** — it swaps both volumes to `PersistentVolumeClaim`s (OACT-9):

```bash
kubectl apply -k k8s/monitoring-persistent   # PVC-backed, retains history
# — vs —
kubectl apply -k k8s/monitoring              # emptyDir, light, ephemeral
```

The overlay's PVCs (`prometheus-tsdb` 8Gi, `grafana-data` 2Gi) declare no
`storageClassName`, so the k3s droplet's default `local-path` provisioner binds
them. On a non-k3s cluster, set an explicit `storageClassName` on the two PVCs in
`k8s/monitoring-persistent/pvcs.yaml`.

## Prerequisites (operator-provisioned, out-of-band)

### 1. Enable the metrics endpoint

The backend `/metrics/` view returns **404** until `METRICS_ENABLED=true`. Patch
the prod ConfigMap (or set it in `k8s/overlays/prod/configmap-patch.yaml`):

```bash
kubectl -n openshiksha-prod patch configmap openshiksha-config \
  --type merge -p '{"data":{"METRICS_ENABLED":"true"}}'
kubectl -n openshiksha-prod rollout restart deploy/backend
```

> Enabling `/metrics/` also makes it reachable through the ingress. **Set
> `METRICS_TOKEN`** (below) so the endpoint isn't openly scrapable.

### 2. Add the secret keys

The stack reads three keys from the existing `openshiksha-secrets` Secret
(documented in [`k8s/base/secret.example.yaml`](../../k8s/base/secret.example.yaml)):

| Key | Consumed by | Notes |
|---|---|---|
| `METRICS_TOKEN` | Prometheus scrape (bearer) | May be empty (then scrapes are unauthenticated); set it when `METRICS_ENABLED=true`. |
| `ALERT_NTFY_URL` | ntfy bridge sidecar | The ntfy topic URL alerts are pushed to (same channel as the ALT-3 uptime probe). |
| `GRAFANA_ADMIN_PASSWORD` | Grafana | Admin login password. |

```bash
kubectl -n openshiksha-prod patch secret openshiksha-secrets --type merge -p '{
  "stringData": {
    "METRICS_TOKEN": "<random-token>",
    "ALERT_NTFY_URL": "https://ntfy.sh/<your-alerts-topic>",
    "GRAFANA_ADMIN_PASSWORD": "<strong-password>"
  }
}'
```

## Deploy

```bash
kubectl apply -k k8s/monitoring
kubectl -n openshiksha-prod rollout status deploy/prometheus
kubectl -n openshiksha-prod rollout status deploy/alertmanager
kubectl -n openshiksha-prod rollout status deploy/grafana
```

## The alert path

```
backend /metrics/  →  Prometheus (scrape + ALT-1 rules)  →  Alertmanager
        →  alert_to_ntfy (sidecar :9098)  →  ntfy (ALERT_NTFY_URL)
```

## "Is it live?" checklist

1. **Metrics endpoint responds** (from inside the cluster, with the token):
   ```bash
   kubectl -n openshiksha-prod exec deploy/backend -- \
     sh -c 'wget -qO- --header "Authorization: Bearer $METRICS_TOKEN" http://backend:8000/metrics/ | head'
   ```
   Expect Prometheus text exposition, not a 404.

2. **Prometheus scrape target is UP**:
   ```bash
   kubectl -n openshiksha-prod port-forward svc/prometheus 9090:9090
   # → http://localhost:9090/targets : openshiksha-backend, prometheus, and
   #                                    alertmanager (OACT-8 self-scrape) should be UP
   # → http://localhost:9090/rules   : the 8 ALT-1 rules + MonitoringTargetDown (OACT-8) loaded
   ```

3. **Alertmanager is reachable** and the bridge is wired:
   ```bash
   kubectl -n openshiksha-prod port-forward svc/alertmanager 9093:9093
   # → http://localhost:9093 : config shows receiver ntfy-bridge → http://alert-to-ntfy:9098/alert
   ```
   Fire a test push through the bridge directly:
   ```bash
   kubectl -n openshiksha-prod exec deploy/alertmanager -c alert-to-ntfy -- \
     python -c "import urllib.request,json; urllib.request.urlopen(urllib.request.Request('http://localhost:9098/alert', data=json.dumps({'alerts':[{'status':'firing','labels':{'severity':'warning','alertname':'TestPing'},'annotations':{'summary':'monitoring stack smoke test'}}]}).encode(), method='POST'))"
   ```
   A `TestPing` push should land in the ntfy topic.

4. **Grafana shows data** (primary access — login-gated public sub-path):
   ```
   # → https://openshiksha.org/grafana  (admin / GRAFANA_ADMIN_PASSWORD)
   # → "OpenShiksha — Overview" dashboard auto-provisioned, panels render
   ```
   The prod overlay's ingress (`k8s/overlays/prod/ingress-patch.yaml`, #494)
   routes `/grafana` → the `grafana` Service, and Grafana serves from that
   sub-path (`GF_SERVER_ROOT_URL` + `GF_SERVER_SERVE_FROM_SUB_PATH=true`).
   **Ordering caveat:** the `/grafana` ingress route auto-deploys with the prod
   overlay, but the `grafana` Service only exists once you have applied
   `k8s/monitoring` (this step's prerequisite) — until then `/grafana` returns
   **503**. If the sub-path misbehaves, fall back to a port-forward:
   ```bash
   kubectl -n openshiksha-prod port-forward svc/grafana 3000:3000
   # → http://localhost:3000 (admin / GRAFANA_ADMIN_PASSWORD)
   ```

5. **Backup freshness gauge reads real data** (after the next nightly backup, or a
   manual `kubectl create job --from=cronjob/postgres-backup backup-manual`):
   ```
   # In Prometheus: openshiksha_backup_age_seconds should be present and small.
   ```

## Tear down

```bash
kubectl delete -k k8s/monitoring
```

This removes only the monitoring stack; the app, backups, and uptime probe (in
the prod overlay) are untouched.
