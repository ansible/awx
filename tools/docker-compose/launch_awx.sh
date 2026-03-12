#!/bin/bash
set +x

bootstrap_development.sh

cd /awx_devel

# Run the given command, usually supervisord
exec "$@"
