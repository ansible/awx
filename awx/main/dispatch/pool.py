import logging
import os
import time

from multiprocessing import Process

from django.conf import settings
from django.db import connection as django_connection
from django.core.cache import cache as django_cache

logger = logging.getLogger('awx.main.commands.run_callback_receiver')


class PoolWorker(object):
    """
    A simple wrapper around a multiprocessing.Process that tracks a worker child process.

    The worker process runs the provided target function and tracks its creation time.
    """

    def __init__(self, target, args, **kwargs):
        self.process = Process(target=target, args=args)
        self.process.daemon = True
        self.creation_time = time.monotonic()

    def start(self):
        self.process.start()


class WorkerPool(object):
    """
    Creates a pool of forked PoolWorkers.

    Each worker process runs the provided target function in an isolated process.
    The pool manages spawning, tracking, and stopping worker processes.

    Example:
        pool = WorkerPool(workers_num=4)  # spawn four worker processes
    """

    pool_cls = PoolWorker
    debug_meta = ''

    def __init__(self, workers_num=None):
        self.name = settings.CLUSTER_HOST_ID
        self.pid = os.getpid()
        self.workers_num = workers_num or settings.JOB_EVENT_WORKERS
        self.workers = []

    def __len__(self):
        return len(self.workers)

    def init_workers(self, target, *target_args):
        self.target = target
        self.target_args = target_args
        for idx in range(self.workers_num):
            self.up()

    def up(self):
        idx = len(self.workers)
        # It's important to close these because we're _about_ to fork, and we
        # don't want the forked processes to inherit the open sockets
        # for the DB and cache connections (that way lies race conditions)
        django_connection.close()
        django_cache.close()
        worker = self.pool_cls(self.target, (idx,) + self.target_args)
        self.workers.append(worker)
        try:
            worker.start()
        except Exception:
            logger.exception('could not fork')
        else:
            logger.debug('scaling up worker pid:{}'.format(worker.process.pid))
        return idx, worker

    def stop(self, signum):
        try:
            for worker in self.workers:
                os.kill(worker.pid, signum)
        except Exception:
            logger.exception('could not kill {}'.format(worker.pid))
