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

# This file will be re-written when the dispatcher calls reconfigure_rsyslog(),
# but it needs to exist when supervisor initially starts rsyslog to prevent the
# container from crashing. This was the most minimal config I could get working.
cat << EOF > /var/lib/awx/rsyslog/rsyslog.conf
action(type="omfile" file="/dev/null")
EOF

exec supervisord -c /etc/supervisor_rsyslog.conf

