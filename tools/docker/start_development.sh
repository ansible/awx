#!/bin/bash

/etc/init.d/postgresql start
/etc/init.d/redis-server start
nohup mongod &

/bin/bash
