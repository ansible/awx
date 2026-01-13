# Copyright (c) 2018 Ansible by Red Hat
# All Rights Reserved.

import os
import logging
import signal
import sys
import redis
import time
from queue import Empty as QueueEmpty

from django import db


from awx.main.utils.redis import get_redis_client
from awx.main.dispatch.pool import WorkerPool
from awx.main.utils.db import set_connection_name

if 'run_callback_receiver' in sys.argv:
    logger = logging.getLogger('awx.main.commands.run_callback_receiver')
else:
    logger = logging.getLogger('awx.main.dispatch')


def signame(sig):
    return dict((k, v) for v, k in signal.__dict__.items() if v.startswith('SIG') and not v.startswith('SIG_'))[sig]


class WorkerSignalHandler:
    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        signal.signal(signal.SIGINT, self.exit_gracefully)

    def exit_gracefully(self, *args, **kwargs):
        self.kill_now = True


class AWXConsumerBase(object):
    last_stats = time.time()

    def __init__(self, name, worker, queues=[], pool=None):
        self.should_stop = False

        self.name = name
        self.total_messages = 0
        self.queues = queues
        self.worker = worker
        self.pool = pool
        if pool is None:
            self.pool = WorkerPool()
        self.pool.init_workers(self.worker.work_loop)
        self.redis = get_redis_client()

    def run(self, *args, **kwargs):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)

        # Child should implement other things here

    def stop(self, signum, frame):
        self.should_stop = True
        logger.warning('received {}, stopping'.format(signame(signum)))
        self.worker.on_stop()
        raise SystemExit()


class AWXConsumerRedis(AWXConsumerBase):
    def run(self, *args, **kwargs):
        super(AWXConsumerRedis, self).run(*args, **kwargs)
        self.worker.on_start()
        logger.info(f'Callback receiver started with pid={os.getpid()}')
        db.connection.close()  # logs use database, so close connection

        while True:
            time.sleep(60)


class BaseWorker(object):
    def read(self):
        raise NotImplemented()

    def work_loop(self, idx, *args):
        ppid = os.getppid()
        signal_handler = WorkerSignalHandler()
        set_connection_name('worker')  # set application_name to distinguish from other dispatcher processes
        while not signal_handler.kill_now:
            # if the parent PID changes, this process has been orphaned
            # via e.g., segfault or sigkill, we should exit too
            if os.getppid() != ppid:
                break
            try:
                body = self.read()
                if body == 'QUIT':
                    break
            except QueueEmpty:
                continue
            except Exception:
                logger.exception("Exception on worker {}, reconnecting: ".format(idx))
                continue
            try:
                for conn in db.connections.all():
                    # If the database connection has a hiccup during the prior message, close it
                    # so we can establish a new connection
                    conn.close_if_unusable_or_obsolete()
                self.perform_work(body, *args)
            except Exception:
                logger.exception(f'Unhandled exception in perform_work in worker pid={os.getpid()}')

        logger.debug('worker exiting gracefully pid:{}'.format(os.getpid()))

    def perform_work(self, body):
        raise NotImplementedError()

    def on_start(self):
        pass

    def on_stop(self):
        pass
