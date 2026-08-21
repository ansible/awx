#!/usr/bin/env bash
if [ `id -u` -ge 500 ]; then
    echo "awx:x:`id -u`:`id -g`:,,,:/var/lib/awx:/bin/bash" >> /tmp/passwd
    cat /tmp/passwd > /etc/passwd
    rm /tmp/passwd
fi

if [ -n "${AWX_KUBE_DEVEL}" ]; then
    pushd /awx_devel
    make awx-link
    popd

    export SDB_NOTIFY_HOST=$MY_POD_IP
fi

set -e

wait-for-migrations

RECEPTOR_CONF="/etc/receptor/receptor.conf"
RECEPTOR_WAIT_TIMEOUT=120
elapsed=0
while [ ! -f "$RECEPTOR_CONF" ]; do
    if [ "$elapsed" -ge "$RECEPTOR_WAIT_TIMEOUT" ]; then
        echo "Timed out waiting for $RECEPTOR_CONF after ${RECEPTOR_WAIT_TIMEOUT}s" >&2
        exit 1
    fi
    echo "Waiting for $RECEPTOR_CONF to be created..." >&2
    sleep 2
    elapsed=$((elapsed + 2))
done

awx-manage provision_instance

exec supervisord -c /etc/supervisord_task.conf
