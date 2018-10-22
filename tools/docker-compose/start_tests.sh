#!/bin/bash
set +x

if [ `id -u` -ge 500 ] || [ -z "${CURRENT_UID}" ]; then
    echo "awx:x:`id -u`:`id -g`:,,,:/tmp:/bin/bash" >> /tmp/passwd
    cat /tmp/passwd > /etc/passwd
    rm /tmp/passwd
fi

cd /awx_devel
make clean
cp -R /tmp/awx.egg-info /awx_devel/ || true
sed -i "s/placeholder/$(cat /awx_devel/VERSION)/" /awx_devel/awx.egg-info/PKG-INFO
cp /tmp/awx.egg-link /venv/awx/lib/python3.6/site-packages/awx.egg-link

cp awx/settings/local_settings.py.docker_compose awx/settings/local_settings.py
make "${1:-test}"
