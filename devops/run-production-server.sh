#!/usr/bin/env bash

# Usage: devops/run-production-server.sh (from root dir)
nginx
gunicorn openshiksha.wsgi -c devops/gunicorn_conf.py