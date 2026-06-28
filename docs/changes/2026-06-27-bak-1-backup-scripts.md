# BAK-1 — Postgres backup/restore scripts + version-matched dump image

**Date:** 2026-06-27
**Classification:** New (Production Observability — Batch 3, Backups & DR drill)
**Initiative:** [Production Observability & Operational Readiness](../initiatives/2026-production-observability.md)

## Summary

OpenShiksha runs live in production on a single `postgres:15-alpine` StatefulSet
with **zero backups** — one bad migration or volume loss wipes every teacher's
questions and every student's submission/proficiency history, unrecoverably. This
PR lays the **foundation** for Batch 3: the dump/restore tooling and a
version-matched container image. It touches nothing live (pure files); the
nightly CronJob (BAK-3), local restore drill (BAK-2), and freshness metric
(BAK-4) build on top of it.

## What changed

- **`scripts/backup/pg_backup.sh`** — `set -euo pipefail`. Custom-format
  `pg_dump --no-owner --no-privileges` → `gzip -9` → timestamped
  `openshiksha-YYYYmmddTHHMMSSZ.dump.gz`. Uploads via the MinIO client (`mc`) to
  an S3-compatible bucket, then prunes objects older than `RETENTION_DAYS`
  (default 14). **Local mode:** when `S3_ENDPOINT` is empty it keeps the dump on
  disk and skips upload — this is the branch the BAK-2 drill exercises so the
  *same* script is tested end-to-end without cloud creds. Secrets are never
  echoed (pg_dump reads the connection URI / PG* env directly; `mc alias set`
  reads creds from args into a private `MC_CONFIG_DIR`).
- **`scripts/backup/pg_restore.sh`** — inverse path. Downloads a named or
  `latest` object (or reads `LOCAL_FILE`), gunzips, and
  `pg_restore --clean --if-exists --no-owner`. **Refuses to run without
  `CONFIRM=1`** to guard against a fat-fingered prod restore.
- **`backend/Dockerfile.backup`** — `FROM postgres:15-alpine` so `pg_dump`
  matches the prod server's major version exactly (an older pg_dump refuses to
  run against a newer server). Adds a **pinned** static `mc` binary (not aws-cli
  — one static binary vs. a heavy install), copies both scripts, runs as the
  unprivileged `postgres` user, default `ENTRYPOINT` = `pg_backup.sh`.
- **`.gitattributes`** (new) — forces `*.sh` / `Dockerfile*` to LF so a CRLF
  shebang from a Windows checkout can never break execution inside the container.

## What changed from legacy and why

Nothing to port — the Django 1.11 monolith (now under `legacy/`) had **no**
backup story; data integrity relied on the host disk. This is greenfield ops. The
improvement is an off-site, retained, **version-matched** dump on a schedule,
plus (in BAK-2) a restore that has actually been run rather than a backup nobody
has restored from.

## Technical details

- Custom format (`-Fc`) is selectively restorable and already compressed; the
  extra `gzip -9` shrinks the transferred artefact and yields a single file.
  `pipefail` ensures a `pg_dump` failure fails the pipe even though `gzip` is
  last.
- `latest` resolution sorts object names lexicographically — the
  `openshiksha-YYYYmmddT…` timestamp sorts chronologically by construction.
- `mc` version is pinned (`ARG MC_VERSION`) for reproducible image builds; the
  build verifies `mc --version` before baking it in.

## Tests / validation

- `bash -n` syntax check clean on both scripts (shellcheck not installed in the
  build env; the CI `k8s`/lint lanes are unaffected — these are new infra files).
- `pg_backup.sh --help` prints usage; `pg_restore.sh` without `CONFIRM=1` fails
  closed with a clear error and non-zero exit.
- Image build (`docker build -f backend/Dockerfile.backup .`) is exercised by CI
  once the publish matrix entry lands in BAK-3.

## Migration notes

None — no Django models or migrations in this PR.

## Next steps

- **BAK-2** — `scripts/backup/drill.sh`: local seed → backup (local mode) → drop
  → restore → assert row-count parity (the "tested restore runbook" DoD clause).
- **BAK-3** — prod-overlay-only `CronJob` + CI publish of this image + `S3_*`
  secret keys documented.
- **BAK-4** — `BackupRun` model + `openshiksha_backup_age_seconds` freshness
  gauge on the MET-2 collector.
- **BAK-5** — `docs/ops/backups.md` runbook + ledger.
