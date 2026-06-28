# Backups & disaster-recovery runbook

OpenShiksha's live data (every teacher's questions, every student's submission and
proficiency history) lives in a **single Postgres StatefulSet** on the prod
droplet. This runbook covers the **off-site nightly backup** and the **tested
restore drill** that protect it (Production Observability Batch 3, BAK-1..5).

Everything here is **additive and prod-scoped**: qa/dev kustomize builds are
byte-for-byte unchanged and run no backup; no secret is committed.

## What is backed up, where, how often

| | |
|---|---|
| **Source** | The prod Postgres DB (`DATABASE_URL` in `openshiksha-secrets`). |
| **Artefact** | A custom-format `pg_dump` (`-Fc --no-owner --no-privileges`), gzipped: `openshiksha-YYYYmmddTHHMMSSZ.dump.gz`. |
| **Destination** | An S3-compatible bucket (intended: a **DigitalOcean Spaces** bucket), prefix `postgres/`. |
| **Schedule** | Nightly **02:00 UTC** via the prod `CronJob` `postgres-backup`. |
| **Retention** | `RETENTION_DAYS` (default **14**) — older objects pruned each run. |
| **RPO** | ≤ 24 h (nightly). Tighten by raising the schedule frequency if needed. |
| **RTO** | Minutes — a single `pg_restore` of one dump file (see below). |

## Components

| File | Role |
|------|------|
| [`scripts/backup/pg_backup.sh`](../../scripts/backup/pg_backup.sh) | `pg_dump \| gzip` → S3 upload via `mc` → retention prune. **Local mode** when `S3_ENDPOINT=""` (keeps the dump on disk, no upload). |
| [`scripts/backup/pg_restore.sh`](../../scripts/backup/pg_restore.sh) | Download latest/named (or `LOCAL_FILE`) → `pg_restore --clean --if-exists`. **Refuses without `CONFIRM=1`.** |
| [`scripts/backup/drill.sh`](../../scripts/backup/drill.sh) | Local, tested backup→restore round-trip asserting row-count parity. |
| [`backend/Dockerfile.backup`](../../backend/Dockerfile.backup) | `FROM postgres:15-alpine` (version-matched `pg_dump`) + pinned static `mc`. Published by CI as `ghcr.io/openshiksha/openshiksha-backup`. |
| [`k8s/overlays/prod/backup-cronjob.yaml`](../../k8s/overlays/prod/backup-cronjob.yaml) | The nightly prod `CronJob` (prod overlay only). |

> **Why `postgres:15-alpine`?** `pg_dump` refuses to dump a server whose major
> version is newer than the client. Pinning the image to the prod server's major
> guarantees a working dump. Bump both together on a Postgres major upgrade.

## Secrets

The four `S3_*` keys are added (empty) to
[`k8s/base/secret.example.yaml`](../../k8s/base/secret.example.yaml) and populated
out-of-band into `openshiksha-secrets` in the **prod** namespace only:

```
S3_ENDPOINT   e.g. https://blr1.digitaloceanspaces.com
S3_BUCKET     e.g. openshiksha-backups
S3_ACCESS_KEY <spaces access key>
S3_SECRET_KEY <spaces secret key>
```

`DATABASE_URL` is the existing key. qa/dev don't run the CronJob, so they don't
need these. Never commit real values (sealed-secrets/external-secrets is the
long-term home).

## Restore — local drill (proves the path)

Run against the docker-compose Postgres. **Non-destructive** — it only touches a
throwaway scratch DB (`openshiksha_drill`):

```bash
docker compose up -d postgres
bash scripts/backup/drill.sh        # seed → backup → wipe → restore → assert parity
```

A green run proves `pg_backup.sh` + `pg_restore.sh` round-trip and that a restore
actually reconstitutes the data. (Negative check: corrupt the dump between steps
and the drill exits non-zero.) **Follow-up:** wire this into CI as a smoke job
against an ephemeral compose Postgres so the restore path stays continuously
proven.

## Restore — production (real recovery)

A one-off restore Job using the same image and `pg_restore.sh`:

```bash
kubectl -n openshiksha-prod run pg-restore --rm -it --restart=Never \
  --image=ghcr.io/openshiksha/openshiksha-backup:prod \
  --env="CONFIRM=1" \
  --env="OBJECT=latest" \
  --env="S3_ENDPOINT=$S3_ENDPOINT" --env="S3_BUCKET=$S3_BUCKET" \
  --env="S3_ACCESS_KEY=$S3_ACCESS_KEY" --env="S3_SECRET_KEY=$S3_SECRET_KEY" \
  --env="TARGET_DB=$DATABASE_URL" \
  --command -- /usr/local/bin/pg_restore.sh
```

`CONFIRM=1` is mandatory (the script refuses without it). `OBJECT=latest`
restores the newest dump; pass an explicit key to restore a specific point.
**This is destructive** — it `--clean`s the target DB. Scale the backend/celery
down first to stop writes, restore, then scale back up.

## Freshness metric (feeds Batch 4 alerting)

The CronJob records each successful run as a `core.BackupRun` row (via
`manage.py record_backup_run`). The MET-2 `BusinessMetricsCollector` then exposes,
on the gated `/metrics` endpoint:

| Metric | Meaning |
|--------|---------|
| `openshiksha_backup_age_seconds` | Seconds since the most recent **successful** backup. **Absent** when none has been recorded (honest — never a fake-fresh `0`). |
| `openshiksha_backup_last_success_timestamp` | Unix timestamp of the last success (`0` when none). |

**Suggested Batch-4 alert:** page when
`openshiksha_backup_age_seconds > 129600` (36 h) **or** the series is absent for a
sustained period — either means backups have silently stopped.

> **Follow-up:** the freshness gauge only lights up once `record_backup_run` is
> wired into the backup script/Job (a thin `python manage.py record_backup_run …
> || true` after a successful `mc cp`). Until then the gauge is honestly absent.

## See also
- [`docs/ops/metrics.md`](metrics.md) — the `/metrics` runbook (enable steps,
  scrape config, metric catalogue).
- [Initiative doc](../initiatives/2026-production-observability.md) — Batch 3
  backlog + progress ledger.
