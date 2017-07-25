#!/bin/bash

# Code duplicated from start_development.sh
cp -R /tmp/ansible_awx.egg-info /awx_devel/ || true
sed -i "s/placeholder/$(git describe --long | sed 's/\./\\./g')/" /awx_devel/ansible_awx.egg-info/PKG-INFO
cp /tmp/ansible-awx.egg-link /venv/awx/lib/python2.7/site-packages/ansible-awx.egg-link

cp -f awx/settings/local_settings.py.docker_compose awx/settings/local_settings.py

/bin/bash -c "$@"
