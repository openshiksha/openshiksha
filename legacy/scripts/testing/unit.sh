#!/usr/bin/env bash

# Usage: scripts/testing/unit.sh (from root directory)

set -e

python -Wall manage.py test core.tests.unit --noinput