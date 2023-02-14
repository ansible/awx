#!/bin/bash
set +x

: "${SOURCES:=_sources}"
export SOURCES
bootstrap_development.sh

cd /awx_devel
# Start the services
exec make supervisor
