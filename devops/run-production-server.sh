#!/usr/bin/env bash

# Usage: devops/run-production-server.sh (from Dockerfile WorkDir)

devops/prep-production-server.sh

# Run nginx and gunicorn
nginx
gunicorn openshiksha.wsgi -c devops/gunicorn_conf.py