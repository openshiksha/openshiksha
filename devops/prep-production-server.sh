#!/usr/bin/env bash

# Usage: devops/prep-production-server.sh (from Dockerfile WorkDir)

# Setup static files
./manage.py collectstatic --noinput

# Run migrations
./manage.py migrate --noinput

# Initialize db with critical data
./manage.py loaddata skeleton openshiksha_school question_bank celery_beat

# Set secure passwords for superuser and OpenShiksha School Admin
./manage.py runscript scripts.security.secure_admin_accounts



