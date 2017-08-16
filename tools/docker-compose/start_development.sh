#!/bin/bash
set +x

/bootstrap_development.sh

cd /awx_devel
# Start the services
if [ -f "/awx_devel/tools/docker-compose/use_dev_supervisor.txt" ]; then
    make supervisor
else
    honcho start -f "tools/docker-compose/Procfile"
fi
