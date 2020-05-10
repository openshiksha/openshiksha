#!/usr/bin/env bash

# Usage: devops/compile-nginx.sh (from root dir)

COMPILED_NGINX_CONF=devops/nginx.compiled.conf

echo 'compiling nginx conf'
cp devops/nginx.conf $COMPILED_NGINX_CONF
sed -i "s|__SERVER_NAMES__|${SERVER_NAMES}|g" $COMPILED_NGINX_CONF