import logging

from multiprocessing import Process

from django.conf import settings
from django.db import connection as django_connection
from django.core.cache import cache as django_cache

logger = logging.getLogger('awx.main.commands.run_callback_receiver')


class PoolWorker(object):
    """
    A simple wrapper around a multiprocessing.Process that tracks a worker child process.

    The worker process runs the provided target function.
    """

    def __init__(self, target, args):
        self.process = Process(target=target, args=args)
        self.process.daemon = True

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

    def __init__(self, workers_num=None):
        self.workers_num = workers_num or settings.JOB_EVENT_WORKERS

    def init_workers(self, target):
        for idx in range(self.workers_num):
            # It's important to close these because we're _about_ to fork, and we
            # don't want the forked processes to inherit the open sockets
            # for the DB and cache connections (that way lies race conditions)
            django_connection.close()
            django_cache.close()
            worker = PoolWorker(target, (idx,))
            try:
                worker.start()
            except Exception:
                logger.exception('could not fork')
            else:
                logger.debug('scaling up worker pid:{}'.format(worker.process.pid))
