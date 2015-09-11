#!/usr/bin/env bash

# Usage: devops/deploy.sh (from hwcentral root dir)

sudo supervisorctl stop gunicorn
git pull origin master
scripts/collab/virtualenv_cleanup.sh
devops/prep-deploy.sh
nginx -s reload
# allow log files to be created inside devops directory
chmod 777 devops/
sudo supervisorctl update gunicorn
sudo supervisorctl start gunicorn