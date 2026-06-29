# ALT-5 — Alerting runbook + Sentry routing + Batch 4 close-out

**Date:** 2026-06-28
**Initiative:** Production Observability & Operational Readiness — Batch 4 (Uptime & alerting)
**Classification:** New / Docs

## Summary

The documentation + close-out increment that completes Production Observability
Batch 4 and reaches the initiative's **North Star**.

- **`docs/ops/alerting.md`** (sibling of `metrics.md` + `backups.md`):
  - **Two-layer TL;DR** — the standalone ALT-3 uptime probe alerts *today* with no
    monitoring stack; the rule-based ALT-1/2/4 path is validated drop-in, dormant
    until an operator deploys Prometheus + Alertmanager.
  - **Alert catalogue** — a table for each ALT-1 alert: metric/expr → threshold →
    severity → **first-response action** (BackupStale → check CronJob + run the
    BAK-2 drill; GradeQueueBacklog → check the Celery worker; TargetDown → check
    the pod + readiness; etc.), with the honest-no-op note for the Celery alerts.
  - **Routing** — the `Prometheus → Alertmanager → alert_to_ntfy.py → ntfy` path,
    the severity→ntfy mapping (resolved never pages), the email alternative, and
    the `ALERT_NTFY_URL` secret.
  - **Uptime probe** — what ALT-3 covers, its cadence, and the
    debounce trade-off vs the rule-based `OpenShikshaTargetDown`.
  - **Sentry alerts** — how to wire Sentry's own issue-alert rules (error-rate
    spike, new-issue) to the same email/ntfy channel, turning the OBS-3/OBS-5
    Sentry capture into *alerting*.
  - Thresholds framed as **operator-tuned starting points**.

## Close-out

- `docs/initiatives/2026-production-observability.md`: added the **Batch 4 backlog
  table** (ALT-1..5, mirroring Batches 1–3), flipped the **Later batches** Batch-4
  bullet to ✅ SHIPPED, appended the **ALT-1..5 ledger row** (the "instrument →
  measure → recover → get told" loop + two lessons: gate config-as-code like
  manifests; a deployed floor alarm beats an undeployed perfect one), and set the
  header **Status → ✅ North Star reached**.
- `docs/initiatives/STATUS.md`: new top "Last updated" block (initiative **Done**),
  priority-table row Status **Active → Done**, headline appended with Batch 4,
  Next → **promote a fresh top initiative** (no unblocked next bet remains).

## Honest follow-ups (stated explicitly, not blocking close)

- Prometheus + Alertmanager are **not deployed** in `k8s/` yet — ALT-1/2/4 are
  validated drop-in artifacts an operator activates; the standalone ALT-3 probe is
  the only piece that alerts with zero stack.
- Wire `VITE_SENTRY_DSN` into the CI frontend build once a DSN is provisioned.
- Wire `record_backup_run` into the backup Job so prod populates the freshness gauge.

## Validation

- Markdown links to `metrics.md` / `backups.md` resolve; the artifact paths the
  runbook documents are created by ALT-1/2/3 (present on qa once those merge).
- No code paths touched.
