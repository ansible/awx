#!/usr/bin/env bash
if [ `id -u` -ge 10000 ]; then
    echo "awx:x:`id -u`:`id -g`:,,,:/var/lib/awx:/bin/bash" >> /tmp/passwd
    cat /tmp/passwd > /etc/passwd
    rm /tmp/passwd
fi
awx-manage collectstatic --noinput --clear
supervisord -c /supervisor.conf
