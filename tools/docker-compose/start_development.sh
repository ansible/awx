#!/bin/bash
set +x

# Wait for the databases to come up
ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=postgres port=5432" all
ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=memcached port=11211" all
ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=${RABBITMQ_HOST} port=5672" all

# In case Tower in the container wants to connect to itself, use "docker exec" to attach to the container otherwise
# TODO: FIX
#/etc/init.d/ssh start

ansible -i "127.0.0.1," -c local -v -m postgresql_user -U postgres -a "name=awx-dev password=AWXsome1 login_user=postgres login_host=postgres" all
ansible -i "127.0.0.1," -c local -v -m postgresql_db -U postgres -a "name=awx-dev owner=awx-dev login_user=postgres login_host=postgres" all

# Move to the source directory so we can bootstrap
if [ -f "/tower_devel/manage.py" ]; then
    cd /tower_devel
elif [ -f "/tower_devel/ansible-tower/manage.py" ]; then
    cd /tower_devel/ansible-tower
else
    echo "Failed to find tower source tree, map your development tree volume"
fi

cp -nR /tmp/ansible_tower.egg-info /tower_devel/ || true

# Check if we need to build dependencies
#if [ -f "awx/lib/.deps_built" ]; then
#    echo "Skipping dependency build - remove awx/lib/.deps_built to force a rebuild"
#else
#SWIG_FEATURES="-cpperraswarn -includeall -D__`uname -m`__ -I/usr/include/openssl" make requirements_dev
#    touch awx/lib/.deps_built
#fi

cp /tmp/ansible-tower.egg-link /venv/tower/lib/python2.7/site-packages/ansible-tower.egg-link

# Tower bootstrapping
make version_file
make migrate
make init

# Start the service
make honcho
