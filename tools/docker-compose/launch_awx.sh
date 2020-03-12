#!/bin/bash
set +x

bootstrap_development.sh

cd /awx_devel
# Start the services
exec tini -- make supervisor
