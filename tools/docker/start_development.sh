#!/bin/bash

/etc/init.d/ssh start
/etc/init.d/postgresql start
/etc/init.d/redis-server start
nohup mongod &
if ! [ -d "/tower_devel/awx/lib/site-packages" ]; then
    ln -s /tower/awx/lib/site-packages /tower_devel/awx/lib/site-packages
fi
/bin/bash
