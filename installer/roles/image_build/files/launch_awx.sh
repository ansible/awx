#!/usr/bin/env bash
if [ `id -u` -ge 500 ]; then
    echo "awx:x:`id -u`:`id -g`:,,,:/var/lib/awx:/bin/bash" >> /tmp/passwd
    cat /tmp/passwd > /etc/passwd
    rm /tmp/passwd
fi

source /etc/tower/conf.d/environment.sh

ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=$DATABASE_HOST port=$DATABASE_PORT" all
ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=$MEMCACHED_HOST port=$MEMCACHED_PORT" all
ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=$RABBITMQ_HOST port=$RABBITMQ_PORT" all
ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m postgresql_user --become-user postgres -a "name=$DATABASE_NAME password=$DATABASE_PASSWORD encrypted=yes login_user=postgres login_password=$DATABASE_ADMIN_PASSWORD login_host=postgres" all
ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m postgresql_db --become-user postgres -a "name=$DATABASE_NAME owner=$DATABASE_USER login_user=postgres login_host=$DATABASE_HOST login_password=$DATABASE_ADMIN_PASSWORD port=$DATABASE_PORT" all

awx-manage collectstatic --noinput --clear

unset $(cut -d = -f -1 /etc/tower/conf.d/environment.sh)

supervisord -c /supervisor.conf
