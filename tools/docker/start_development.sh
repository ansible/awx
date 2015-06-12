#!/bin/bash

/etc/init.d/ssh start
/etc/init.d/postgresql start
/etc/init.d/redis-server start
nohup mongod &

/bin/bash
