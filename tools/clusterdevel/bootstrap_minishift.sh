#!/bin/bash
set +x

# Wait for the databases to come up
ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=postgresql port=5432" all
ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=localhost port=11211" all
ansible -i "127.0.0.1," -c local -v -m wait_for -a "host=localhost port=5672" all
ansible -i "127.0.0.1," -c local -v -m postgresql_db -U postgres -a "name=awx owner=awx login_user=awx login_password=awx login_host=postgresql" all

# Move to the source directory so we can bootstrap
if [ -f "/awx_devel/manage.py" ]; then
    cd /awx_devel
else
    echo "Failed to find awx source tree, map your development tree volume"
fi

#make awx-link
python setup.py develop
ln -s /awx_devel/tools/rdb.py /venv/awx/lib/python2.7/site-packages/rdb.py || true
yes | cp -rf /awx_devel/tools/docker-compose/supervisor.conf /supervisor.conf

# AWX bootstrapping
make version_file
make migrate
make init

mkdir -p /awx_devel/awx/public/static
mkdir -p /awx_devel/awx/ui/static

cd /awx_devel
# Start the services
if [ -f "/awx_devel/tools/docker-compose/use_dev_supervisor.txt" ]; then
    make supervisor
else
    honcho start -f "tools/docker-compose/Procfile"
fi
