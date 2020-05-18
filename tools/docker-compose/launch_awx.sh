#!/bin/bash
set +x

/awx_devel/tools/docker-compose/bootstrap_development.sh

cd /awx_devel
# Start the services
exec tini -- make supervisor
