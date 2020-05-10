#!/usr/bin/env bash

# Usage: scripts/collab/prep-static.sh (from root dir)

echo 'Removing existing data in dev database'
python manage.py reset_db --noinput
echo 'Updating local dev database'
python manage.py migrate
