#!/usr/bin/env bash
if [ `id -u` -ge 500 ]; then
    echo "awx:x:`id -u`:`id -g`:,,,:/var/lib/awx:/bin/bash" >> /tmp/passwd
    cat /tmp/passwd > /etc/passwd
    rm /tmp/passwd
fi

source /etc/tower/conf.d/environment.sh

ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=$DATABASE_HOST port=$DATABASE_PORT" all
ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=$MEMCACHED_HOST port=$MEMCACHED_PORT" all
ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m postgresql_db --become-user $DATABASE_USER -a "name=$DATABASE_NAME owner=$DATABASE_USER login_user=$DATABASE_USER login_host=$DATABASE_HOST login_password=$DATABASE_PASSWORD port=$DATABASE_PORT" all

awx-manage collectstatic --noinput --clear

unset $(cut -d = -f -1 /etc/tower/conf.d/environment.sh)

supervisord -c /supervisor.conf
