import errno
import logging
import os
import signal
import traceback

from multiprocessing import Process
from multiprocessing import Queue as MPQueue
from Queue import Full as QueueFull

from django.conf import settings
from django.db import connection as django_connection
from django.core.cache import cache as django_cache

logger = logging.getLogger('awx.main.dispatch')


def signame(sig):
    return dict(
        (k, v) for v, k in signal.__dict__.items()
        if v.startswith('SIG') and not v.startswith('SIG_')
    )[sig]


class WorkerPool(object):

    def __init__(self, min_workers=None, queue_size=None):
        self.min_workers = min_workers or settings.JOB_EVENT_WORKERS
        self.queue_size = queue_size or settings.JOB_EVENT_MAX_QUEUE_SIZE

        # self.workers tracks the state of worker running worker processes:
        # [
        #   (total_messages_consumed, multiprocessing.Queue, multiprocessing.Process),
        #   (total_messages_consumed, multiprocessing.Queue, multiprocessing.Process),
        #   (total_messages_consumed, multiprocessing.Queue, multiprocessing.Process),
        #   (total_messages_consumed, multiprocessing.Queue, multiprocessing.Process)
        # ]
        self.workers = []

    def __len__(self):
        return len(self.workers)

    def init_workers(self, target, *target_args):
        def shutdown_handler(active_workers):
            def _handler(signum, frame):
                logger.debug('received shutdown {}'.format(signame(signum)))
                try:
                    for active_worker in active_workers:
                        logger.debug('terminating worker')
                    signal.signal(signum, signal.SIG_DFL)
                    os.kill(os.getpid(), signum) # Rethrow signal, this time without catching it
                except Exception:
                    logger.exception('error in shutdown_handler')
            return _handler

        django_connection.close()
        django_cache.close()
        for idx in range(self.min_workers):
            queue_actual = MPQueue(self.queue_size)
            w = Process(target=target, args=(queue_actual, idx,) + target_args)
            w.start()
            logger.debug('started {}[{}]'.format(target.im_self.__class__.__name__, idx))
            self.workers.append([0, queue_actual, w])

        signal.signal(signal.SIGINT, shutdown_handler([p[2] for p in self.workers]))
        signal.signal(signal.SIGTERM, shutdown_handler([p[2] for p in self.workers]))

    def write(self, preferred_queue, body):
        queue_order = sorted(range(self.min_workers), cmp=lambda x, y: -1 if x==preferred_queue else 0)
        write_attempt_order = []
        for queue_actual in queue_order:
            try:
                worker_actual = self.workers[queue_actual]
                worker_actual[1].put(body, block=True, timeout=5)
                logger.debug('delivered to Worker[{}] qsize {}'.format(
                    queue_actual, worker_actual[1].qsize()
                ))
                worker_actual[0] += 1
                return queue_actual
            except QueueFull:
                pass
            except Exception:
                tb = traceback.format_exc()
                logger.warn("could not write to queue %s" % preferred_queue)
                logger.warn("detail: {}".format(tb))
            write_attempt_order.append(preferred_queue)
        logger.warn("could not write payload to any queue, attempted order: {}".format(write_attempt_order))
        return None

    def stop(self):
        for worker in self.workers:
            messages, queue, process = worker
            try:
                os.kill(process.pid, signal.SIGTERM)
            except OSError as e:
                if e.errno != errno.ESRCH:
                    raise
