#!/usr/bin/env bash

# Usage: scripts/testing/all.sh (from root directory)

set -e

python -Wall manage.py test --noinput
