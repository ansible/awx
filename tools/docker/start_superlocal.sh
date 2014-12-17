#!/bin/bash

/etc/init.d/postgresql start ; /etc/init.d/rabbitmq-server start; cd /tower_devel; make server
