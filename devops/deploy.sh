#!/usr/bin/env bash

# Usage: devops/deploy.sh (from root dir)

sudo nginx -s stop
sudo supervisorctl stop gunicorn
git pull origin master

# only perform time-consuming virtualenv reset if explicitly asked to
if [ "$1" == "-x" ]
    then
    scripts/collab/virtualenv_cleanup.sh
fi

devops/compile-nginx.sh

devops/prep-static.sh
devops/truncate-logs.sh
sudo supervisorctl update gunicorn
sudo supervisorctl start gunicorn
sudo nginx