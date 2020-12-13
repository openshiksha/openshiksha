#!/usr/bin/env bash

# Usage: scripts/collab/virtualenv_cleanup.sh

set -e

echo 'Uninstalling all packages from virtualenv'
echo
pip freeze | xargs pip uninstall -y
echo
echo 'Reinstalling all packages from requirements file'
echo
pip --no-cache-dir install -r pip-requirements.txt

