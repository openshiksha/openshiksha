#!/usr/bin/env bash

# Usage: devops/clearsessions.sh (from root dir and within the virtualenv)

./manage.py clearsessions
echo 'Expired sessions have been cleaned up'