#!/usr/bin/env bash

# Usage: devops/run-gunicorn.sh (from root dir and within virtualenv)

# exec is needed otherwise supervisor just supervises this script and not the forked gunicorn processes
exec gunicorn openshiksha.wsgi -c devops/gunicorn_conf.py



