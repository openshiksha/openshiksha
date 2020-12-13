#!/usr/bin/env bash

# Usage: devops/compile-nginx.sh (from Dockerfile WorkDir)

set -e

COMPILED_NGINX_CONF=devops/nginx.compiled.conf

echo 'compiling nginx conf'
cp devops/nginx.conf $COMPILED_NGINX_CONF

sed -i "s|__WORKDIR__|${WORKDIR}|g" $COMPILED_NGINX_CONF