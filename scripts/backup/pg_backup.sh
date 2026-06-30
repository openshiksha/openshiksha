#!/usr/bin/env bash
#
# pg_backup.sh — version-matched Postgres backup for OpenShiksha.
#
# Dumps the database with a custom-format `pg_dump`, gzips it to a timestamped
# file, and (unless running in local mode) uploads it to an S3-compatible bucket
# via the MinIO client (`mc`), then prunes objects older than RETENTION_DAYS.
#
# This is part of Production Observability Batch 3 (BAK-1). It is invoked by the
# nightly prod CronJob (BAK-3) and exercised end-to-end by the local restore
# drill (BAK-2, scripts/backup/drill.sh).
#
# Configuration (all via environment — secrets are NEVER echoed):
#   DATABASE_URL    postgres://user:pwd@host:port/db   (preferred), OR the
#                   discrete PG* vars below.
#   PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE          (used if DATABASE_URL unset)
#   S3_ENDPOINT     S3-compatible endpoint, e.g. https://blr1.digitaloceanspaces.com
#                   *** Empty/unset ⇒ LOCAL MODE: keep the dump on disk, skip
#                       upload + prune. Used by the drill. ***
#   S3_BUCKET       target bucket name
#   S3_PREFIX       key prefix (default: postgres/)
#   S3_ACCESS_KEY   S3 access key id
#   S3_SECRET_KEY   S3 secret access key
#   RETENTION_DAYS  prune objects older than this many days (default: 14)
#   BACKUP_DIR      where to write the local dump (default: a mktemp dir)
#
# Output: prints the dump filename and (in S3 mode) the uploaded object key.
# Exits non-zero on any failure so the CronJob surfaces it.
#
# Legacy reference: none — the Django 1.11 monolith had no backup story.

set -euo pipefail

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
die() { log "ERROR: $*" >&2; exit 1; }

usage() {
    sed -n '2,40p' "$0" | sed 's/^#//; s/^ //'
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    usage
    exit 0
fi

S3_PREFIX="${S3_PREFIX:-postgres/}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
S3_ENDPOINT="${S3_ENDPOINT:-}"

# Optional BAK-4 hand-off: when RESULT_FILE is set (the prod CronJob's two-phase
# pod, OACT-4), write the outcome to a shared file so the sibling `record`
# container can persist a BackupRun row that populates the
# openshiksha_backup_age_seconds freshness gauge. Best-effort and only on the
# success path — a failed backup exits non-zero before this runs (set -e), so the
# init phase fails the pod and the staleness alert covers it. Never fails the backup.
RESULT_FILE="${RESULT_FILE:-}"
write_result() {
    [[ -n "$RESULT_FILE" ]] || return 0
    printf 'STATUS=%s\nSIZE=%s\nKEY=%s\n' "$1" "${2:-}" "${3:-}" > "$RESULT_FILE" || true
}

# --- Resolve DB connection -------------------------------------------------
# pg_dump reads PG* env vars natively; if DATABASE_URL is given, pg_dump accepts
# a connection URI as a positional argument, so we never have to parse it
# ourselves (and never echo it).
PG_TARGET=()
if [[ -n "${DATABASE_URL:-}" ]]; then
    PG_TARGET=(--dbname "$DATABASE_URL")
else
    [[ -n "${PGDATABASE:-}" ]] || die "Set DATABASE_URL or PGDATABASE (and PGHOST/PGUSER/PGPASSWORD)."
fi

# --- Produce the dump ------------------------------------------------------
TS="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="${BACKUP_DIR:-$(mktemp -d)}"
mkdir -p "$BACKUP_DIR"
DUMP_FILE="$BACKUP_DIR/openshiksha-${TS}.dump.gz"

log "Dumping database → ${DUMP_FILE}"
# custom format is compressed + selectively restorable; --no-owner/--no-privileges
# keep the dump portable across roles. Pipe through gzip for an extra ~size win
# and a single transferable artefact. set -o pipefail catches a pg_dump failure
# even though gzip is last in the pipe.
pg_dump --format=custom --no-owner --no-privileges "${PG_TARGET[@]}" | gzip -9 > "$DUMP_FILE"

SIZE_BYTES="$(wc -c < "$DUMP_FILE" | tr -d ' ')"
[[ "$SIZE_BYTES" -gt 0 ]] || die "Dump is empty — refusing to upload."
log "Dump complete: ${SIZE_BYTES} bytes"

# --- Local mode: stop here -------------------------------------------------
if [[ -z "$S3_ENDPOINT" ]]; then
    log "S3_ENDPOINT unset → LOCAL MODE: dump kept at ${DUMP_FILE} (no upload)."
    write_result success "$SIZE_BYTES" "$DUMP_FILE"
    echo "$DUMP_FILE"
    exit 0
fi

# --- S3 upload + prune -----------------------------------------------------
: "${S3_BUCKET:?Set S3_BUCKET for upload}"
: "${S3_ACCESS_KEY:?Set S3_ACCESS_KEY for upload}"
: "${S3_SECRET_KEY:?Set S3_SECRET_KEY for upload}"
command -v mc >/dev/null 2>&1 || die "mc (MinIO client) not found on PATH."

# mc alias set reads the creds from arguments; we pass them once and never echo.
# Use a private config dir so we don't clobber a developer's ~/.mc.
export MC_CONFIG_DIR="${MC_CONFIG_DIR:-$(mktemp -d)}"
mc alias set osbackup "$S3_ENDPOINT" "$S3_ACCESS_KEY" "$S3_SECRET_KEY" >/dev/null

OBJECT_KEY="${S3_PREFIX}$(basename "$DUMP_FILE")"
log "Uploading → s3://${S3_BUCKET}/${OBJECT_KEY}"
mc cp "$DUMP_FILE" "osbackup/${S3_BUCKET}/${OBJECT_KEY}"

log "Pruning objects older than ${RETENTION_DAYS} days under ${S3_PREFIX}"
# --force is required by mc rm to actually delete; --older-than takes a duration.
mc rm --recursive --force --older-than "${RETENTION_DAYS}d" \
    "osbackup/${S3_BUCKET}/${S3_PREFIX}" 2>/dev/null || \
    log "WARN: prune step reported a non-fatal error (continuing)."

log "Backup OK: ${OBJECT_KEY} (${SIZE_BYTES} bytes)"
write_result success "$SIZE_BYTES" "$OBJECT_KEY"
echo "$OBJECT_KEY"
