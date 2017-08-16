#!/usr/bin/env bash
if [ `id -u` -ge 10000 ]; then
    echo "awx:x:`id -u`:`id -g`:,,,:/var/lib/awx:/bin/bash" >> /tmp/passwd
    cat /tmp/passwd > /etc/passwd
    rm /tmp/passwd
fi
ANSIBLE_REMOTE_TEMP=/tmp ANSIBLE_LOCAL_TEMP=/tmp ansible -i "127.0.0.1," -c local -v -m postgresql_db -U $DATABASE_USER -a "name=$DATABASE_NAME owner=$DATABASE_USER login_user=$DATABASE_USER login_host=$DATABASE_HOST login_password=$DATABASE_PASSWORD" all
awx-manage migrate --noinput --fake-initial
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'root@localhost', 'password')" | awx-manage shell
awx-manage create_preload_data
awx-manage provision_instance --hostname=$(hostname)
awx-manage register_queue --queuename=tower --hostnames=$(hostname)
supervisord -c /supervisor_task.conf
