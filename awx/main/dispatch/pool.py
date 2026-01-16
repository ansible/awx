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
    Used to track a worker child process and its pending and finished messages.

    This class makes use of two distinct multiprocessing.Queues to track state:

    - self.queue: this is a queue which represents pending messages that should
                  be handled by this worker process; as new AMQP messages come
                  in, a pool will put() them into this queue; the child
                  process that is forked will get() from this queue and handle
                  received messages in an endless loop
    - self.finished: this is a queue which the worker process uses to signal
                     that it has finished processing a message

    When a message is put() onto this worker, it is tracked in
    self.managed_tasks.

    Periodically, the worker will call .calculate_managed_tasks(), which will
    cause messages in self.finished to be removed from self.managed_tasks.

    In this way, self.managed_tasks represents a view of the messages assigned
    to a specific process.  The message at [0] is the least-recently inserted
    message, and it represents what the worker is running _right now_
    (self.current_task).

    A worker is "busy" when it has at least one message in self.managed_tasks.
    It is "idle" when self.managed_tasks is empty.
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

    As WorkerPool.write(...) is called (generally, by a kombu consumer
    implementation when it receives an AMQP message), messages are passed to
    one of the multiprocessing Queues where some work can be done on them.

    pool = WorkerPool(min_workers=4)  # spawn four worker processes
    pool.init_workers(MessagePrint().work_loop)
    pool.write(
        0,  # preferred worker 0
        'Hello, World!'
    )
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
            logger.debug('scaling up worker pid:{}'.format(worker.pid))
        return idx, worker

    def stop(self, signum):
        try:
            for worker in self.workers:
                os.kill(worker.pid, signum)
        except Exception:
            logger.exception('could not kill {}'.format(worker.pid))
