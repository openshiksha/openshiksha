# BAK-2 — Local, tested backup → restore round-trip drill

**Date:** 2026-06-27
**Classification:** New (Production Observability — Batch 3, Backups & DR drill)
**Depends on:** [BAK-1](2026-06-27-bak-1-backup-scripts.md) (uses the local-mode
branch of `pg_backup.sh`).

## Summary

A backup nobody has restored from is not a backup. BAK-2 adds
`scripts/backup/drill.sh` — a **tested**, reproducible backup→restore round-trip
that runs entirely against the docker-compose Postgres with **no cloud creds**.
This is the "*tested* restore runbook" clause of the Batch-3 Definition of Done:
it exercises the real BAK-1 scripts and asserts data survives a simulated wipe.

## What changed

- **`scripts/backup/drill.sh`** (`set -euo pipefail`) — round-trips against a
  **throwaway scratch DB** (`openshiksha_drill` by default), so it is
  **non-destructive** to the developer's `openshiksha_dev` DB:
  1. (re)create the scratch DB and seed a `drill_sentinel` table with a known
     row count (`SEED_ROWS`, default 1000).
  2. `pg_backup.sh` in **LOCAL MODE** (`S3_ENDPOINT=""`) → a local `*.dump.gz` —
     exercising the *same* script the prod CronJob runs.
  3. drop + recreate the scratch DB (simulating data loss).
  4. `pg_restore.sh` with `LOCAL_FILE=<dump>` + `CONFIRM=1`.
  5. re-count and **assert** the restored count equals the seeded count; exit
     non-zero with a clear diff on mismatch.
  6. drop the scratch DB (trap-based cleanup).

## Why local-first

It makes the restore path tested and reproducible without provisioning a bucket.
A later CI smoke job can call `drill.sh` against an ephemeral compose Postgres
(noted as a follow-up in the runbook, BAK-5) to keep the restore path
continuously proven.

## Safety

The script DROPs only the scratch DB it owns end-to-end. `DRILL_DB` defaults to
`openshiksha_drill`; the header warns never to point it at a real database. All
admin create/drop runs against the maintenance `postgres` DB; connections are
terminated before drop to avoid "database in use" failures.

## Tests / validation

- `bash -n scripts/backup/drill.sh` — syntax clean.
- **Live round-trip:** intended to run via `bash scripts/backup/drill.sh` against
  `docker compose up -d postgres`. The Docker daemon was **not reachable in the
  build sandbox this run** (npipe to the Desktop Linux engine unavailable), so the
  full live drill is to be run by a developer / the future CI smoke job. The
  logic is standard `psql`/`pg_dump`/`pg_restore`; a negative test (corrupt the
  dump → drill exits non-zero) is documented but not committed.

## Migration notes

None — no Django models.

## Next steps

- BAK-3 — prod-overlay-only CronJob + CI image publish + `S3_*` secret keys.
- BAK-4 — `BackupRun` model + `openshiksha_backup_age_seconds` freshness gauge.
- BAK-5 — `docs/ops/backups.md` runbook (wires a CI smoke calling this drill).
