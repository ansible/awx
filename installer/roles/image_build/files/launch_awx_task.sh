#!/usr/bin/env bash
if [ `id -u` -ge 500 ]; then
    echo "awx:x:`id -u`:`id -g`:,,,:/var/lib/awx:/bin/bash" >> /tmp/passwd
    cat /tmp/passwd > /etc/passwd
    rm /tmp/passwd
fi

ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=$DATABASE_HOST port=$DATABASE_PORT" all
ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=$MEMCACHED_HOST port=11211" all
ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=$RABBITMQ_HOST port=5672" all
ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m postgresql_db --become-user $DATABASE_USER -a "name=$DATABASE_NAME owner=$DATABASE_USER login_user=$DATABASE_USER login_host=$DATABASE_HOST login_password=$DATABASE_PASSWORD port=$DATABASE_PORT" all

if [ -z "$AWX_SKIP_MIGRATIONS" ]; then
    awx-manage migrate --noinput
fi

if [ ! -z "$AWX_ADMIN_USER" ]&&[ ! -z "$AWX_ADMIN_PASSWORD" ]; then
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('$AWX_ADMIN_USER', 'root@localhost', '$AWX_ADMIN_PASSWORD')" | awx-manage shell
    awx-manage create_preload_data
else
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'root@localhost', 'password')" | awx-manage shell
    awx-manage create_preload_data
fi
echo 'from django.conf import settings; x = settings.AWX_TASK_ENV; x["HOME"] = "/var/lib/awx"; settings.AWX_TASK_ENV = x' | awx-manage shell
awx-manage provision_instance --hostname=$(hostname)
awx-manage register_queue --queuename=tower --instance_percent=100
supervisord -c /supervisor_task.conf
