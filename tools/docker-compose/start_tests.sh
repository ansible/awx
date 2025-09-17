#!/bin/bash
set -euo pipefail

cd /awx_devel
make clean
make awx-link

if [[ $# -eq 0 ]]; then
    make test
else
    make "$@"
fi
