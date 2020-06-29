#!/usr/bin/env bash

# Usage: devops/run-production-server.sh (from Dockerfile WorkDir)

# Setup static files
devops/prep-static.sh

# Run nginx and gunicorn
nginx
gunicorn openshiksha.wsgi -c devops/gunicorn_conf.py