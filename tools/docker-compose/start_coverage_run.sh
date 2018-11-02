#!/bin/bash
set +x

/bootstrap_development.sh

cd /awx_devel
# Start the services
export PYTHONIOENCODING=utf_8
honcho start -f "tools/docker-compose/CoverageProcfile"
