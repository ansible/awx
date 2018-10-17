#!/bin/bash
set +x

if [ `id -u` -ge 500 ]; then
    echo "awx:x:`id -u`:`id -g`:,,,:/tmp:/bin/bash" >> /tmp/passwd
    cat /tmp/passwd > /etc/passwd
    rm /tmp/passwd
fi

/bootstrap_development.sh

cd /awx_devel
# Start the services
if [ -f "/awx_devel/tools/docker-compose/use_dev_supervisor.txt" ]; then
    make supervisor
else
    export PYTHONIOENCODING=utf_8
    honcho start -f "tools/docker-compose/Procfile"
fi
