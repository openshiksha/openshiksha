#!/usr/bin/env bash

# Usage: devops/truncate-logs.sh (from root dir)

truncate devops/nginx_access.log --size=0
truncate devops/nginx_error.log --size=0
truncate devops/gunicorn_access.log --size=0
sudo truncate devops/gunicorn_stderr.log --size=0
#truncate devops/cron.log --size=0  # dont truncate cron file log, truncating it seems to break the loggly integration