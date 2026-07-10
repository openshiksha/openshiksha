# Alerting & Uptime Runbook

> **Production Observability — Batch 4 (Uptime & alerting).** Sibling of
> [`metrics.md`](metrics.md) and [`backups.md`](backups.md). This is the
> *self-announcing* half of the operability spine: the last three batches made an
> incident **observable → measurable → recoverable**; this one makes it **push you
> a notification** instead of waiting to be noticed.

## TL;DR — what alerts today, with and without a monitoring stack

OpenShiksha emits rich metrics (see [`metrics.md`](metrics.md)) but **no
Prometheus or Alertmanager is deployed in `k8s/` yet**. So there are two layers:

| Layer | Needs | Status |
|---|---|---|
| **Standalone uptime probe** (ALT-3) | nothing — runs in-cluster | **Active in prod.** A CronJob curls `/healthz/` + `/readyz/` every 5 min and pushes a DOWN alert to ntfy on any failure. |
| **Rule-based alerts** (ALT-1/2/4) | a Prometheus + Alertmanager an operator stands up | **Validated drop-in artifacts.** The rule file, Alertmanager config, and ntfy bridge are committed + CI-linted; they go live the moment an operator deploys the stack and points it at them. |

The honest follow-up: until Prometheus/Alertmanager are actually deployed, the
**standalone ALT-3 probe is the only piece that alerts**. The rule-based path is
ready and tested but dormant. Deploying Prometheus + Alertmanager in `k8s/` is the
tracked operational follow-up (see the initiative doc).

## Alert catalogue (ALT-1 — `docs/ops/prometheus/openshiksha-alerts.yml`)

Every alert fires on a metric the platform **already emits**
(`backend/openshiksha/apps/core/metrics.py`). Thresholds are **conservative
starting points** — tune to your traffic, exactly like the Grafana starter and the
backup-age threshold.

| Alert | Metric / expr | Threshold | Severity | First response |
|---|---|---|---|---|
| `OpenShikshaBackupStale` | `openshiksha_backup_age_seconds` | > 36h (`for 10m`) | critical | Check the `postgres-backup` CronJob (`kubectl get cronjob,jobs -n openshiksha-prod`, `kubectl logs`); confirm S3 creds; run the [BAK-2 restore drill](backups.md) to prove recoverability. |
| `OpenShikshaBackupNeverRun` | `openshiksha_backup_last_success_timestamp == 0` / `absent(...)` | `for 6h` | critical | No backup on record. Fresh deploy ⇒ run a first backup. Otherwise the backup path is broken — check the CronJob + `BackupRun` rows. |
| `OpenShikshaGradeQueueBacklog` | `openshiksha_submissions_pending_grading` | > 50 (`for 30m`) | warning | Check the Celery worker (`kubectl logs deploy/celery`) and the `grade_submission` task; the pipeline may be stalled or under-provisioned. |
| `OpenShikshaCeleryOldestPending` | `openshiksha_celery_oldest_pending_seconds` | > 15m (`for 15m`) | warning | Tasks queue faster than they drain — check worker health + concurrency. *(Only has data under the django-db result backend; see below.)* |
| `OpenShikshaCeleryFailureRate` | `openshiksha_celery_tasks{status="FAILURE"}` ÷ total | > 10% (`for 15m`) | warning | Check worker logs + the failing task type. *(django-db backend only.)* |
| `OpenShikshaHighHTTPErrorRate` | `openshiksha_http_requests_total{status_class="5xx"}` ratio | > 5% (`for 10m`) | critical | Backend serving errors — check pod logs, Sentry, recent deploys. |
| `OpenShikshaHighLatencyP95` | `histogram_quantile(0.95, …_http_request_duration_seconds_bucket)` | > 1.5s (`for 10m`) | warning | Backend slow — check DB load, the grade queue, resource limits. |
| `OpenShikshaTargetDown` | `up{job="openshiksha-backend"} == 0` | `for 5m` | critical | `/metrics` (and likely the app) unreachable — check the pod, readiness probe, ingress. The ALT-3 uptime probe is the no-Prometheus complement to this. |

**Honest no-ops:** `OpenShikshaCeleryOldestPending` and
`OpenShikshaCeleryFailureRate` only carry data when Celery persists results to the
DB (`CELERY_RESULT_BACKEND` is the `django-db` backend, MET-3). Under the default
Redis backend the `openshiksha_celery_*` series are empty and these two never fire
— flipping the backend lights them up automatically.

## Routing (ALT-2 — Alertmanager → ntfy)

ntfy is not a native Alertmanager receiver, so a tiny stdlib bridge translates
Alertmanager's webhook JSON into a one-line ntfy push.

```
Prometheus (rules)  ──fires──▶  Alertmanager  ──webhook──▶  alert_to_ntfy.py  ──POST──▶  ntfy topic
   ALT-1 rule file              ALT-2 config                 ALT-2 bridge                (phone / desktop)
```

- **`docs/ops/alertmanager/alertmanager.yml`** — a `route` (grouped by
  `alertname`/`severity`) to a single `webhook_configs` receiver pointed at the
  bridge (`http://alert-to-ntfy:9098/alert`). A commented `email_configs` block
  shows the e-mail alternative.
- **`scripts/ops/alert_to_ntfy.py`** — dependency-light stdlib bridge (no new pip
  dep). Run it as a sidecar / one-off Deployment next to Alertmanager:
  ```bash
  ALERT_NTFY_URL="https://ntfy.sh/<your-alerts-topic>" \
      python3 scripts/ops/alert_to_ntfy.py        # listens on :9098
  ```
- **severity → ntfy:** critical ⇒ high priority + 🚨; warning ⇒ default + ⚠️;
  **resolved ⇒ min priority + ✅ (never pages, regardless of original severity)**.
- **Secret:** `ALERT_NTFY_URL` lives in `openshiksha-secrets` (server-side only —
  a ntfy topic URL is a *write capability* to the channel; the bridge never logs
  it). Documented (empty) in `k8s/base/secret.example.yaml`.

## Uptime probe (ALT-3 — the floor-level alarm)

`k8s/overlays/prod/uptime-probe-cronjob.yaml` runs
`scripts/ops/uptime_probe.sh` (baked into the BAK-1 backup image, which already
has `curl`) **every 5 minutes**:

- Curls `${PROBE_BASE_URL}/healthz/` and `/readyz/` (in-cluster, `http://backend:8000`).
- On **any** non-200 (or connection failure) ⇒ one high-priority ntfy push naming
  the failing endpoint + code, and exits non-zero so the Job is marked failed
  (also visible via the Batch-2 Job/Celery visibility).
- Success path is **silent** (no per-run spam).

Prod-overlay-only (qa/dev kustomize output is byte-for-byte unchanged). It needs
**no Prometheus** — this is the "is the site up?" alarm that works before any
monitoring stack exists.

**Trade-off vs the rule path:** the probe has no debounce, so a transient blip can
push every 5 min. That's an accepted cost for a dependency-free floor alarm; the
rule-based `OpenShikshaTargetDown` debounces with a `for: 5m` window. Run **both**
once Prometheus is deployed — they cover different failure modes (the probe checks
readiness end-to-end; `up == 0` checks scrape reachability).

## Sentry alerts (lighting up the OBS-3/OBS-5 investment)

Backend (OBS-3) and frontend (OBS-5) errors already flow to Sentry when the DSNs
are set. Capture is not alerting — wire Sentry's **own** issue-alert rules so an
error spike *pushes*:

1. In each Sentry project → **Alerts → Create Alert**.
2. Useful starters: **"Number of errors > N in 1h"** (error-rate spike) and
   **"A new issue is created"** (first sighting of a novel exception).
3. Route the alert action to **e-mail** and/or a **webhook** pointed at the same
   `alert_to_ntfy.py` bridge (or ntfy's own webhook), so Sentry alerts land in the
   same channel as the metric alerts.

This turns the OBS-3/OBS-5 Sentry capture into *alerting*, closing the loop from
"an exception was recorded" to "someone was told."

## Validation (CI — ALT-4 `alerting-lint` job)

`.github/workflows/ci-cd.yaml` gates the config-as-code so it can't silently rot:

- `promtool check rules` + `promtool test rules` (the `.test.yml` fixture asserts
  `OpenShikshaBackupStale` fires at 37h, not 1h).
- `amtool check-config` on the Alertmanager config.
- `pytest scripts/ops/tests/test_alert_to_ntfy.py` on the bridge formatter.

## Operational follow-up (not blocking)

- **Deploy Prometheus + Alertmanager in `k8s/`** so ALT-1/2/4's drop-in artifacts
  go live. Until then the standalone ALT-3 probe is the active alarm.
- **Tune thresholds** to real traffic once there's a baseline (same framing as the
  Grafana starter).
