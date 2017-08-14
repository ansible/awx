# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging
import signal
from uuid import UUID
from multiprocessing import Process
from multiprocessing import Queue as MPQueue
from Queue import Empty as QueueEmpty
from Queue import Full as QueueFull
import os

from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.db import connection as django_connection
from django.db import DatabaseError
from django.core.cache import cache as django_cache

# AWX
from awx.main.models import * # noqa

logger = logging.getLogger('awx.main.commands.run_callback_receiver')


class WorkerSignalHandler:

    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args, **kwargs):
        self.kill_now = True


class CallbackBrokerWorker(ConsumerMixin):
    def __init__(self, connection, use_workers=True):
        self.connection = connection
        self.worker_queues = []
        self.total_messages = 0
        self.init_workers(use_workers)

    def init_workers(self, use_workers=True):
        def shutdown_handler(active_workers):
            def _handler(signum, frame):
                try:
                    for active_worker in active_workers:
                        active_worker.terminate()
                    signal.signal(signum, signal.SIG_DFL)
                    os.kill(os.getpid(), signum) # Rethrow signal, this time without catching it
                except Exception:
                    logger.exception('Error in shutdown_handler')
            return _handler

        if use_workers:
            django_connection.close()
            django_cache.close()
            for idx in range(settings.JOB_EVENT_WORKERS):
                queue_actual = MPQueue(settings.JOB_EVENT_MAX_QUEUE_SIZE)
                w = Process(target=self.callback_worker, args=(queue_actual, idx,))
                w.start()
                if settings.DEBUG:
                    logger.info('Started worker %s' % str(idx))
                self.worker_queues.append([0, queue_actual, w])
        elif settings.DEBUG:
            logger.warn('Started callback receiver (no workers)')

        signal.signal(signal.SIGINT, shutdown_handler([p[2] for p in self.worker_queues]))
        signal.signal(signal.SIGTERM, shutdown_handler([p[2] for p in self.worker_queues]))

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[Queue(settings.CALLBACK_QUEUE,
                                       Exchange(settings.CALLBACK_QUEUE, type='direct'),
                                       routing_key=settings.CALLBACK_QUEUE)],
                         accept=['json'],
                         callbacks=[self.process_task])]

    def process_task(self, body, message):
        if "uuid" in body and body['uuid']:
            try:
                queue = UUID(body['uuid']).int % settings.JOB_EVENT_WORKERS
            except Exception:
                queue = self.total_messages % settings.JOB_EVENT_WORKERS
        else:
            queue = self.total_messages % settings.JOB_EVENT_WORKERS
        self.write_queue_worker(queue, body)
        self.total_messages += 1
        message.ack()

    def write_queue_worker(self, preferred_queue, body):
        queue_order = sorted(range(settings.JOB_EVENT_WORKERS), cmp=lambda x, y: -1 if x==preferred_queue else 0)
        write_attempt_order = []
        for queue_actual in queue_order:
            try:
                worker_actual = self.worker_queues[queue_actual]
                worker_actual[1].put(body, block=True, timeout=5)
                worker_actual[0] += 1
                return queue_actual
            except QueueFull:
                pass
            except Exception:
                import traceback
                tb = traceback.format_exc()
                logger.warn("Could not write to queue %s" % preferred_queue)
                logger.warn("Detail: {}".format(tb))
            write_attempt_order.append(preferred_queue)
        logger.warn("Could not write payload to any queue, attempted order: {}".format(write_attempt_order))
        return None

    def callback_worker(self, queue_actual, idx):
        signal_handler = WorkerSignalHandler()
        while not signal_handler.kill_now:
            try:
                body = queue_actual.get(block=True, timeout=1)
            except QueueEmpty:
                continue
            except Exception as e:
                logger.error("Exception on worker thread, restarting: " + str(e))
                continue
            try:
                if 'job_id' not in body and 'ad_hoc_command_id' not in body:
                    raise Exception('Payload does not have a job_id or ad_hoc_command_id')
                if settings.DEBUG:
                    from pygments import highlight
                    from pygments.lexers import PythonLexer
                    from pygments.formatters import Terminal256Formatter
                    from pprint import pformat
                    logger.info('Body: {}'.format(
                        highlight(pformat(body, width=160), PythonLexer(), Terminal256Formatter(style='friendly'))
                    ))
                try:
                    if 'job_id' in body:
                        JobEvent.create_from_data(**body)
                    elif 'ad_hoc_command_id' in body:
                        AdHocCommandEvent.create_from_data(**body)
                except DatabaseError as e:
                    logger.error('Database Error Saving Job Event: {}'.format(e))
            except Exception as exc:
                import traceback
                tb = traceback.format_exc()
                logger.error('Callback Task Processor Raised Exception: %r', exc)
                logger.error('Detail: {}'.format(tb))


class Command(NoArgsCommand):
    '''
    Save Job Callback receiver (see awx.plugins.callbacks.job_event_callback)
    Runs as a management command and receives job save events.  It then hands
    them off to worker processors (see Worker) which writes them to the database
    '''
    help = 'Launch the job callback receiver'

    def handle_noargs(self, **options):
        with Connection(settings.BROKER_URL) as conn:
            try:
                worker = CallbackBrokerWorker(conn)
                worker.run()
            except KeyboardInterrupt:
                print('Terminating Callback Receiver')
