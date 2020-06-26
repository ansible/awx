#!/bin/bash
set +x

# Wait for the databases to come up
ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=postgres port=5432" all
ansible -i "127.0.0.1," -c local -v -m wait_for -a "path=/var/run/redis/redis.sock" all

# In case AWX in the container wants to connect to itself, use "docker exec" to attach to the container otherwise
# TODO: FIX
#/etc/init.d/ssh start

ansible -i "127.0.0.1," -c local -v -m postgresql_user --become-user postgres -a "name=awx-dev password=AWXsome1 encrypted=yes login_user=postgres login_password=postgrespass login_host=postgres" all
ansible -i "127.0.0.1," -c local -v -m postgresql_db --become-user postgres -a "name=awx-dev owner=awx-dev login_user=postgres login_password=postgrespass login_host=postgres" all

# Move to the source directory so we can bootstrap
if [ -f "/awx_devel/manage.py" ]; then
    cd /awx_devel
else
    echo "Failed to find awx source tree, map your development tree volume"
fi

make awx-link

# AWX bootstrapping
make version_file
make migrate
make init

mkdir -p /awx_devel/awx/public/static
mkdir -p /awx_devel/awx/ui/static
mkdir -p /awx_devel/awx/ui_next/build/static
