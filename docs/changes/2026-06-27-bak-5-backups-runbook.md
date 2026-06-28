# BAK-5 — Backups & DR runbook + ledger close-out

**Date:** 2026-06-27
**Classification:** New / Docs (Production Observability — Batch 3, Backups & DR drill)

## Summary

Closes Batch 3. Adds the operator-facing backups runbook and marks the initiative
ledger + STATUS board: **Batch 3 shipped, Next → Batch 4 (Uptime & alerting)**.

## What changed

- **`docs/ops/backups.md`** (new) — what/where/when is backed up, RPO (≤24 h) /
  RTO, the component map (scripts, image, CronJob), the `S3_*` secret keys, the
  **local restore drill** (`drill.sh`) and the **prod restore** (`kubectl run`
  Job with `pg_restore.sh` + `CONFIRM=1`), and the `openshiksha_backup_age_seconds`
  freshness metric with the suggested **36 h** Batch-4 alert threshold. Sibling to
  `docs/ops/metrics.md`.
- **`docs/initiatives/2026-production-observability.md`** — BAK-1..5 marked ✅
  with PR links; "Later batches" Batch 3 → SHIPPED; a Progress-Ledger row added
  capturing the two ops lessons (kustomize overlay-file security boundary;
  honest empty-history for the freshness gauge).
- **`docs/initiatives/STATUS.md`** — Production Observability row: Batch 3 folded
  into headline progress; **Next increment → Batch 4**, carrying the open
  follow-ups (wire `VITE_SENTRY_DSN`; wire `record_backup_run` into the
  script/Job; add a CI smoke running `drill.sh`).

## Follow-ups recorded (not blocking Batch 3 close)

1. Wire `python manage.py record_backup_run … || true` into the backup
   script/Job so prod actually populates the freshness gauge.
2. Add a CI smoke that runs `drill.sh` against an ephemeral compose Postgres.
3. (carried) Wire `VITE_SENTRY_DSN` into the CI frontend build once a DSN exists.

## Tests / validation

Docs-only — no code paths. Relative links resolve from `docs/ops/`.

## Next steps

Batch 4 — Uptime & alerting (external `/healthz/` + `/readyz/` checks; alert
routing on Sentry error-rate + probe-fail + the Batch-2 metrics + the Batch-3
`openshiksha_backup_age_seconds` freshness gauge).
