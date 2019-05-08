#!/bin/bash
set +x

/bootstrap_development.sh

cd /awx_devel
# Start the services
make supervisor
