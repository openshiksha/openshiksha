#!/usr/bin/env bash

# use this script to automate updating your dev setup with the master openshiksha branch
# Usage: scripts/collab/update.sh (run from root directory)

echo 'RUN THIS SCRIPT FROM ROOT DIRECTORY ONLY'
echo
echo 'If that is not the case, quit this script and switch to the root directory'
echo
echo 'Press enter to continue or ctrl+C to quit...'
read -p "$*"
echo
echo 'Continuing...'
echo

git status

echo 'Please check the above git status output ^'
echo
echo 'YOU SHOULD BE ON MASTER AND HAVE NO CHANGES'
echo
echo 'If that is not the case, quit this script and first commit your changes on your dev branch and switch to master'
echo
echo 'Press enter to continue or ctrl+C to quit...'
read -p "$*"
echo
echo 'Continuing...'
echo

echo -n "VIRTUAL ENV = "
echo $VIRTUAL_ENV

echo 'Please check the above virtualenv output ^'
echo
echo 'YOU SHOULD BE IN THE VIRTUALENV FOR THIS PROJECT'
echo
echo 'If that is not the case, quit this script and switch to the correct virtualenv'
echo
echo 'Press enter to continue or ctrl+C to quit...'
read -p "$*"
echo
echo 'Continuing...'
echo

echo 'Updating virtualenv'
pip install -r pip-requirements.txt
echo

scripts/database/data-update.sh
echo 'Loading initial data'
python manage.py loaddata skeleton
python manage.py loaddata schools

echo
echo
echo 'Script completed. Dont forget to rebase your dev branch(es) on top of the current master by:'
echo '1. git checkout <dev-branch>'
echo '2. git rebase master'
echo '3. git push -f origin <dev-branch>'

