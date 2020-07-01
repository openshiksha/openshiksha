#!/usr/bin/env bash

# Usage: scripts/testing/integration.sh (from root directory)

python -Wall manage.py test core.tests.integration --noinput