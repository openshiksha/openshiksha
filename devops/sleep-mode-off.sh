#!/usr/bin/env bash

# Usage: devops/sleep-mode-off.sh (from root dir)

# stop the gunicorn server
sudo supervisorctl stop gunicorn

# unset the sleep mode flag
unset OPENSHIKSHA_SLEEP_MODE

# start the gunicorn server
sudo supervisorctl start gunicorn

