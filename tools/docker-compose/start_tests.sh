#!/bin/bash
set +x

cd /awx_devel
make clean
make awx-link

cp awx/settings/local_settings.py.docker_compose awx/settings/local_settings.py
make "${1:-test}"
