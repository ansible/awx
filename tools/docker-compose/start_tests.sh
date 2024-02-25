#!/bin/bash
set +x

cd /awx_devel
make clean
make awx-link

if [[ ! $@ ]]; then
    make test
else
    make $@
fi
