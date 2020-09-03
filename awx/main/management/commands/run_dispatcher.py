# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import logging

from django.conf import settings
from django.core.cache import cache as django_cache
from django.core.management.base import BaseCommand
from django.db import connection as django_connection

from awx.main.dispatch import get_local_queuename, reaper
from awx.main.dispatch.control import Control
from awx.main.dispatch.pool import AutoscalePool
from awx.main.dispatch.worker import AWXConsumerPG, TaskWorker
from awx.main.dispatch import periodic

logger = logging.getLogger('awx.main.dispatch')


def construct_bcast_queue_name(common_name):
    return common_name + '_' + settings.CLUSTER_HOST_ID


class Command(BaseCommand):
    help = 'Launch the task dispatcher'

    def add_arguments(self, parser):
        parser.add_argument('--status', dest='status', action='store_true',
                            help='print the internal state of any running dispatchers')
        parser.add_argument('--running', dest='running', action='store_true',
                            help='print the UUIDs of any tasked managed by this dispatcher')
        parser.add_argument('--reload', dest='reload', action='store_true',
                            help=('cause the dispatcher to recycle all of its worker processes;'
                                  'running jobs will run to completion first'))

    def handle(self, *arg, **options):
        if options.get('status'):
            print(Control('dispatcher').status())
            return
        if options.get('running'):
            print(Control('dispatcher').running())
            return
        if options.get('reload'):
            return Control('dispatcher').control({'control': 'reload'})

        # It's important to close these because we're _about_ to fork, and we
        # don't want the forked processes to inherit the open sockets
        # for the DB and cache connections (that way lies race conditions)
        django_connection.close()
        django_cache.close()

        # spawn a daemon thread to periodically enqueues scheduled tasks
        # (like the node heartbeat)
        periodic.run_continuously()

        reaper.reap()
        consumer = None

        try:
            queues = ['tower_broadcast_all', get_local_queuename()]
            consumer = AWXConsumerPG(
                'dispatcher',
                TaskWorker(),
                queues,
                AutoscalePool(min_workers=4)
            )
            consumer.run()
        except KeyboardInterrupt:
            logger.debug('Terminating Task Dispatcher')
            if consumer:
                consumer.stop()
