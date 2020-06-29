#!/usr/bin/env bash

# Usage: scripts/database/data-update.sh (from root dir)

echo 'Removing existing data in database'
python manage.py reset_db --noinput
echo 'Updating local database'
python manage.py migrate
