#!/bin/bash
set +x

cd /awx_devel
make clean
make awx-link

cp tools/docker-compose/_sources/local_settings.py awx/settings/local_settings.py

if [[ ! $@ ]]; then
    make test
else
    make $@
fi
