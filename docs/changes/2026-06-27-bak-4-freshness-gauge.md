# BAK-4 — Backup-freshness gauge + BackupRun model

**Date:** 2026-06-27
**Classification:** New (Production Observability — Batch 3, Backups & DR drill)
**Reuses:** the MET-2 `BusinessMetricsCollector` (Batch 2).

## Summary

Threads the backup signal into the metric surface so Batch 4 alerting has
something concrete to fire on (e.g. "no successful backup in 36 h"). Adds a tiny
`BackupRun` audit model, a `record_backup_run` command the CronJob calls on
success, and an on-scrape `openshiksha_backup_age_seconds` gauge. Fully
env-gated — unchanged behaviour unless `METRICS_ENABLED`.

## What changed

- **`core.BackupRun`** model (`backup_runs` table) — `created_at` (indexed),
  `status` (success/failure), `size_bytes` (nullable), `object_key`. Append-only,
  no PII. Migration `0030_backuprun`. Admin-registered (read-only).
- **`manage.py record_backup_run`** — `--status/--size/--key`; writes one
  `BackupRun` row. The CronJob calls it best-effort after a successful upload (a
  recording failure must never fail the backup — caller chains `|| true`).
- **`openshiksha_backup_age_seconds`** + **`openshiksha_backup_last_success_timestamp`**
  added to the `BusinessMetricsCollector` — computed on-scrape from the newest
  *successful* `BackupRun`, same gated read-only pattern as the other business
  gauges. **No new endpoint, no new dependency.**

## Honest empty-history handling

When no successful backup has ever been recorded, the age family is **omitted**
(and the timestamp reads `0`) rather than emitting a misleading "0 seconds old".
An absent series is honest; a fake-fresh `0` would mask a total backup outage.
Failure-only history is treated the same as no history.

## Tests

`openshiksha/apps/core/tests/test_metrics_backup.py` (5 tests, all green; full
metrics suite 18/18):
- `record_backup_run` writes a row with the given fields.
- gauge + timestamp present when a successful `BackupRun` exists.
- age is reasonable (~2 h backdated → ~7200 s).
- empty history → age family omitted, timestamp `0.0`.
- failure-only runs do **not** count as a successful backup.

## Migration notes

`0030_backuprun` — additive (new table only); backwards-compatible.

## Next steps

- BAK-5 — `docs/ops/backups.md` runbook documents the metric + the suggested
  Batch-4 alert threshold, and a follow-up wires `record_backup_run` into the
  backup script/Job so prod actually populates the gauge.
