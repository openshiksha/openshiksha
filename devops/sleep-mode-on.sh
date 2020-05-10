#!/usr/bin/env bash

# Usage: devops/sleep-mode-on.sh (from root dir)

# stop the gunicorn server
sudo supervisorctl stop gunicorn

# set the sleep mode flag
export OPENSHIKSHA_SLEEP_MODE=on

# start the gunicorn server
sudo supervisorctl start gunicorn