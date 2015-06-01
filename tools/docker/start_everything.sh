#!/bin/bash

/etc/init.d/postgresql start
/etc/init.d/redis-server start
nohup mongod --smallfiles &

(cd /tower_devel && make server &&
/bin/bash)
