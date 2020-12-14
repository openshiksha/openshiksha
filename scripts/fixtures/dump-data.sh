#!/usr/bin/env bash

# run this script from root directory to dump the current mysql data
# Usage: scripts/fixtures/dump-data.sh [<path to output file>]

set -e

OUTFILE=${1:-"db_dump.json"}

# excluding session history and admin actions history and
# permissions data - which is recreated automatically on migrate
./manage.py runscript scripts.fixtures.dump_data --script-args="#o $OUTFILE"

echo "Test data has been dumped to $OUTFILE"
