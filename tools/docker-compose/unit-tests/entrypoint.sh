#!/bin/bash

# Code duplicated from start_development.sh
cp -R /tmp/awx.egg-info /awx_devel/ || true
sed -i "s/placeholder/$(cat /awx_devel/VERSION)/" /awx_devel/awx.egg-info/PKG-INFO
cp /tmp/awx.egg-link /venv/awx/lib/python3.6/site-packages/awx.egg-link

cp -f awx/settings/local_settings.py.docker_compose awx/settings/local_settings.py

/bin/bash -c "$@"
