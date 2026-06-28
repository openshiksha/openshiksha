#!/usr/bin/env bash
#
# drill.sh — local, tested backup -> restore round-trip drill (BAK-2).
#
# Proves scripts/backup/pg_backup.sh + pg_restore.sh actually round-trip,
# reproducibly, with NO cloud creds — the "*tested* restore runbook" half of the
# Batch-3 Definition of Done. A backup nobody has restored from is not a backup.
#
# Flow (entirely against the docker-compose Postgres, NON-destructive to the dev
# DB — it only touches a throwaway scratch DB):
#   1. (re)create a scratch DB                     (default: openshiksha_drill)
#   2. seed a sentinel table with a known row count
#   3. pg_backup.sh in LOCAL MODE (S3_ENDPOINT="") -> a local *.dump.gz
#   4. drop + recreate the scratch DB (now empty)
#   5. pg_restore.sh LOCAL_FILE=<dump> CONFIRM=1 into the scratch DB
#   6. re-count and ASSERT the row count matches; non-zero exit + diff on mismatch
#   7. drop the scratch DB
#
# *** Safety: NEVER point DRILL_DB at a database you care about — step 4 DROPs it.
#     It defaults to `openshiksha_drill`, which this script owns end-to-end. ***
#
# Requires the postgres client tools (psql/createdb/dropdb/pg_dump/pg_restore) on
# PATH and a reachable compose Postgres. A future CI smoke job can call this
# (out of scope here; see docs/ops/backups.md).
#
# Config (env, with compose defaults):
#   PGHOST(localhost) PGPORT(5432) PGUSER(openshiksha) PGPASSWORD(openshiksha)
#   DRILL_DB(openshiksha_drill)  SEED_ROWS(1000)

set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export PGHOST="${PGHOST:-localhost}"
export PGPORT="${PGPORT:-5432}"
export PGUSER="${PGUSER:-openshiksha}"
export PGPASSWORD="${PGPASSWORD:-openshiksha}"
DRILL_DB="${DRILL_DB:-openshiksha_drill}"
SEED_ROWS="${SEED_ROWS:-1000}"

log() { printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*"; }
die() { log "ERROR: $*" >&2; exit 1; }

# All admin (create/drop) ops connect to the maintenance `postgres` DB.
psql_admin() { psql --no-psqlrc -v ON_ERROR_STOP=1 -d postgres "$@"; }
psql_drill() { psql --no-psqlrc -v ON_ERROR_STOP=1 -d "$DRILL_DB" "$@"; }

count_rows() { psql_drill -tAc "SELECT count(*) FROM drill_sentinel;"; }

recreate_db() {
    # Terminate any leftover connections, then drop + create afresh.
    psql_admin -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity \
        WHERE datname = '${DRILL_DB}' AND pid <> pg_backend_pid();" >/dev/null
    psql_admin -c "DROP DATABASE IF EXISTS \"${DRILL_DB}\";" >/dev/null
    psql_admin -c "CREATE DATABASE \"${DRILL_DB}\";" >/dev/null
}

cleanup() {
    psql_admin -c "DROP DATABASE IF EXISTS \"${DRILL_DB}\";" >/dev/null 2>&1 || true
    [[ -n "${WORK_DIR:-}" ]] && rm -rf "$WORK_DIR"
}
trap cleanup EXIT

command -v psql >/dev/null 2>&1 || die "psql not on PATH (need postgres client tools)."
WORK_DIR="$(mktemp -d)"
DRILL_URL="postgresql://${PGUSER}:${PGPASSWORD}@${PGHOST}:${PGPORT}/${DRILL_DB}"

log "=== BAK-2 backup/restore drill against ${PGHOST}:${PGPORT} (scratch DB: ${DRILL_DB}) ==="

# 1 + 2 — fresh scratch DB seeded with a known row count.
log "Step 1/2: (re)create scratch DB and seed ${SEED_ROWS} sentinel rows"
recreate_db
psql_drill -c "CREATE TABLE drill_sentinel (id int PRIMARY KEY, payload text NOT NULL);" >/dev/null
psql_drill -c "INSERT INTO drill_sentinel \
    SELECT g, md5(g::text) FROM generate_series(1, ${SEED_ROWS}) g;" >/dev/null
BEFORE="$(count_rows)"
log "Seeded row count: ${BEFORE}"
[[ "$BEFORE" == "$SEED_ROWS" ]] || die "Seed mismatch: expected ${SEED_ROWS}, got ${BEFORE}"

# 3 — back up the scratch DB in LOCAL MODE (no S3).
log "Step 3: pg_backup.sh (LOCAL MODE)"
DUMP_FILE="$(S3_ENDPOINT="" BACKUP_DIR="$WORK_DIR" DATABASE_URL="$DRILL_URL" \
    bash "${HERE}/pg_backup.sh" | tail -1)"
[[ -f "$DUMP_FILE" ]] || die "Backup did not produce a dump file (got: ${DUMP_FILE})"
log "Dump written: ${DUMP_FILE} ($(wc -c < "$DUMP_FILE" | tr -d ' ') bytes)"

# 4 — wipe: drop + recreate empty.
log "Step 4: drop + recreate scratch DB (simulating data loss)"
recreate_db
EMPTY="$(psql_drill -tAc \
    "SELECT count(*) FROM information_schema.tables WHERE table_name='drill_sentinel';")"
[[ "$EMPTY" == "0" ]] || die "Scratch DB not actually empty after recreate"

# 5 — restore from the dump.
log "Step 5: pg_restore.sh (LOCAL_FILE, CONFIRM=1)"
CONFIRM=1 LOCAL_FILE="$DUMP_FILE" TARGET_DB="$DRILL_URL" bash "${HERE}/pg_restore.sh"

# 6 — assert parity.
log "Step 6: assert restored row count == seeded row count"
AFTER="$(count_rows)"
log "Restored row count: ${AFTER}"
if [[ "$AFTER" != "$BEFORE" ]]; then
    die "ROUND-TRIP FAILED: seeded ${BEFORE} rows, restored ${AFTER}."
fi

log "=== DRILL PASSED: ${BEFORE} rows survived backup -> wipe -> restore intact. ==="
