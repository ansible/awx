# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import os
import logging
from multiprocessing import Process

from django.conf import settings
from django.core.cache import cache as django_cache
from django.core.management.base import BaseCommand
from django.db import connection as django_connection, connections
from kombu import Exchange, Queue

from awx.main.utils.handlers import AWXProxyHandler
from awx.main.dispatch import get_local_queuename, reaper
from awx.main.dispatch.control import Control
from awx.main.dispatch.kombu import Connection
from awx.main.dispatch.pool import AutoscalePool
from awx.main.dispatch.worker import AWXConsumer, TaskWorker

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

    def beat(self):
        from celery import Celery
        from celery.beat import PersistentScheduler
        from celery.apps import beat

        class AWXScheduler(PersistentScheduler):

            def __init__(self, *args, **kwargs):
                self.ppid = os.getppid()
                super(AWXScheduler, self).__init__(*args, **kwargs)

            def setup_schedule(self):
                super(AWXScheduler, self).setup_schedule()
                self.update_from_dict(settings.CELERYBEAT_SCHEDULE)

            def tick(self, *args, **kwargs):
                if os.getppid() != self.ppid:
                    # if the parent PID changes, this process has been orphaned
                    # via e.g., segfault or sigkill, we should exit too
                    raise SystemExit()
                return super(AWXScheduler, self).tick(*args, **kwargs)

            def apply_async(self, entry, producer=None, advance=True, **kwargs):
                for conn in connections.all():
                    # If the database connection has a hiccup, re-establish a new
                    # connection
                    conn.close_if_unusable_or_obsolete()
                task = TaskWorker.resolve_callable(entry.task)
                result, queue = task.apply_async()

                class TaskResult(object):
                    id = result['uuid']

                return TaskResult()

        sched_file = '/var/lib/awx/beat.db'
        app = Celery()
        app.conf.BROKER_URL = settings.BROKER_URL
        app.conf.CELERY_TASK_RESULT_EXPIRES = False

        # celery in py3 seems to have a bug where the celerybeat schedule
        # shelve can become corrupted; we've _only_ seen this in Ubuntu and py36
        # it can be avoided by detecting and removing the corrupted file
        # at some point, we'll just stop using celerybeat, because it's clearly
        # buggy, too -_-
        #
        # https://github.com/celery/celery/issues/4777
        sched = AWXScheduler(schedule_filename=sched_file, app=app)
        try:
            sched.setup_schedule()
        except Exception:
            logger.exception('{} is corrupted, removing.'.format(sched_file))
            sched._remove_db()
        finally:
            try:
                sched.close()
            except Exception:
                logger.exception('{} failed to sync/close'.format(sched_file))

        beat.Beat(
            30,
            app,
            schedule=sched_file, scheduler_cls=AWXScheduler
        ).run()

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
        # for the DB and memcached connections (that way lies race conditions)
        django_connection.close()
        django_cache.close()
        beat = Process(target=self.beat)
        beat.daemon = True
        beat.start()

        reaper.reap()
        consumer = None

        # don't ship external logs inside the dispatcher's parent process
        # this exists to work around a race condition + deadlock bug on fork
        # in cpython itself:
        # https://bugs.python.org/issue37429
        AWXProxyHandler.disable()
        with Connection(settings.BROKER_URL) as conn:
            try:
                bcast = 'tower_broadcast_all'
                queues = [
                    Queue(q, Exchange(q), routing_key=q)
                    for q in (settings.AWX_CELERY_QUEUES_STATIC + [get_local_queuename()])
                ]
                queues.append(
                    Queue(
                        construct_bcast_queue_name(bcast),
                        exchange=Exchange(bcast, type='fanout'),
                        routing_key=bcast,
                        reply=True
                    )
                )
                consumer = AWXConsumer(
                    'dispatcher',
                    conn,
                    TaskWorker(),
                    queues,
                    AutoscalePool(min_workers=4)
                )
                consumer.run()
            except KeyboardInterrupt:
                logger.debug('Terminating Task Dispatcher')
                if consumer:
                    consumer.stop()
