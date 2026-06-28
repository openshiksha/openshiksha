#!/usr/bin/env bash
#
# pg_restore.sh — restore an OpenShiksha Postgres backup produced by pg_backup.sh.
#
# Downloads a named (or `latest`) dump from the S3-compatible bucket — or reads a
# local file in LOCAL MODE — gunzips it, and restores into the target database
# with `pg_restore --clean --if-exists`.
#
# *** DESTRUCTIVE: this DROPS and recreates the target schema. It refuses to run
#     without CONFIRM=1 to guard against a fat-fingered prod restore. ***
#
# Part of Production Observability Batch 3 (BAK-1). The local restore drill
# (BAK-2) calls this in LOCAL MODE; the prod runbook (BAK-5) calls it via a
# one-off kubectl Job.
#
# Configuration (environment):
#   CONFIRM=1       REQUIRED — acknowledges the destructive restore.
#   TARGET_DB       postgres URI or dbname to restore INTO (preferred), OR PG* vars.
#   PGHOST PGPORT PGUSER PGPASSWORD PGDATABASE   (used if TARGET_DB unset)
#   LOCAL_FILE      path to a local *.dump.gz — sets LOCAL MODE, skips S3.
#   S3_ENDPOINT S3_BUCKET S3_PREFIX S3_ACCESS_KEY S3_SECRET_KEY   (S3 mode)
#   OBJECT         object key under S3_PREFIX, or "latest" (default: latest).
#
# Legacy reference: none — greenfield ops.

set -euo pipefail

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
die() { log "ERROR: $*" >&2; exit 1; }

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    sed -n '2,30p' "$0" | sed 's/^#//; s/^ //'
    exit 0
fi

[[ "${CONFIRM:-}" == "1" ]] || die "Refusing to restore without CONFIRM=1 (this DROPS data)."

S3_PREFIX="${S3_PREFIX:-postgres/}"
OBJECT="${OBJECT:-latest}"

# --- Resolve restore target ------------------------------------------------
PG_TARGET=()
if [[ -n "${TARGET_DB:-}" ]]; then
    PG_TARGET=(--dbname "$TARGET_DB")
else
    [[ -n "${PGDATABASE:-}" ]] || die "Set TARGET_DB or PGDATABASE (and PGHOST/PGUSER/PGPASSWORD)."
fi

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

# --- Obtain the dump -------------------------------------------------------
if [[ -n "${LOCAL_FILE:-}" ]]; then
    [[ -f "$LOCAL_FILE" ]] || die "LOCAL_FILE not found: ${LOCAL_FILE}"
    GZ="$LOCAL_FILE"
    log "LOCAL MODE: restoring from ${GZ}"
else
    : "${S3_ENDPOINT:?Set S3_ENDPOINT (or LOCAL_FILE for local restore)}"
    : "${S3_BUCKET:?Set S3_BUCKET}"
    : "${S3_ACCESS_KEY:?Set S3_ACCESS_KEY}"
    : "${S3_SECRET_KEY:?Set S3_SECRET_KEY}"
    command -v mc >/dev/null 2>&1 || die "mc (MinIO client) not found on PATH."

    export MC_CONFIG_DIR="${MC_CONFIG_DIR:-$(mktemp -d)}"
    mc alias set osbackup "$S3_ENDPOINT" "$S3_ACCESS_KEY" "$S3_SECRET_KEY" >/dev/null

    if [[ "$OBJECT" == "latest" ]]; then
        # Newest object under the prefix by lexicographic name (timestamps sort
        # chronologically by construction: openshiksha-YYYYmmddT...).
        OBJECT="$(mc ls "osbackup/${S3_BUCKET}/${S3_PREFIX}" | awk '{print $NF}' | sort | tail -1)"
        [[ -n "$OBJECT" ]] || die "No backups found under ${S3_PREFIX}"
        log "Resolved latest backup: ${OBJECT}"
    fi
    GZ="${WORK_DIR}/$(basename "$OBJECT")"
    log "Downloading s3://${S3_BUCKET}/${S3_PREFIX}${OBJECT}"
    mc cp "osbackup/${S3_BUCKET}/${S3_PREFIX}${OBJECT}" "$GZ"
fi

# --- Restore ---------------------------------------------------------------
DUMP="${WORK_DIR}/restore.dump"
log "Decompressing dump"
gunzip -c "$GZ" > "$DUMP"

log "Restoring (pg_restore --clean --if-exists)"
# --clean --if-exists drops existing objects first so a restore over a populated
# DB is idempotent; --no-owner matches the dump flags. A non-zero pg_restore exit
# on benign "does not exist" notices is suppressed by --if-exists.
pg_restore --clean --if-exists --no-owner "${PG_TARGET[@]}" "$DUMP"

log "Restore complete."
