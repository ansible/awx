# Copyright (c) 2018 Ansible by Red Hat
# All Rights Reserved.

import os
import logging
import signal
import sys
from uuid import UUID
from queue import Empty as QueueEmpty

from django import db
from kombu import Producer
from kombu.mixins import ConsumerMixin

from awx.main.dispatch.pool import WorkerPool

if 'run_callback_receiver' in sys.argv:
    logger = logging.getLogger('awx.main.commands.run_callback_receiver')
else:
    logger = logging.getLogger('awx.main.dispatch')


def signame(sig):
    return dict(
        (k, v) for v, k in signal.__dict__.items()
        if v.startswith('SIG') and not v.startswith('SIG_')
    )[sig]


class WorkerSignalHandler:

    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)

    def exit_gracefully(self, *args, **kwargs):
        self.kill_now = True


class AWXConsumer(ConsumerMixin):

    def __init__(self, name, connection, worker, queues=[], pool=None):
        self.connection = connection
        self.total_messages = 0
        self.queues = queues
        self.worker = worker
        self.pool = pool
        if pool is None:
            self.pool = WorkerPool()
        self.pool.init_workers(self.worker.work_loop)

    def get_consumers(self, Consumer, channel):
        logger.debug(self.listening_on)
        return [Consumer(queues=self.queues, accept=['json'],
                         callbacks=[self.process_task])]

    @property
    def listening_on(self):
        return 'listening on {}'.format([
            '{} [{}]'.format(q.name, q.exchange.type) for q in self.queues
        ])

    def control(self, body, message):
        logger.warn(body)
        control = body.get('control')
        if control in ('status', 'running'):
            producer = Producer(
                channel=self.connection,
                routing_key=message.properties['reply_to']
            )
            if control == 'status':
                msg = '\n'.join([self.listening_on, self.pool.debug()])
            elif control == 'running':
                msg = []
                for worker in self.pool.workers:
                    worker.calculate_managed_tasks()
                    msg.extend(worker.managed_tasks.keys())
            producer.publish(msg)
        elif control == 'reload':
            for worker in self.pool.workers:
                worker.quit()
        else:
            logger.error('unrecognized control message: {}'.format(control))
        message.ack()

    def process_task(self, body, message):
        if 'control' in body:
            try:
                return self.control(body, message)
            except Exception:
                logger.exception("Exception handling control message:")
                return
        if len(self.pool):
            if "uuid" in body and body['uuid']:
                try:
                    queue = UUID(body['uuid']).int % len(self.pool)
                except Exception:
                    queue = self.total_messages % len(self.pool)
            else:
                queue = self.total_messages % len(self.pool)
        else:
            queue = 0
        self.pool.write(queue, body)
        self.total_messages += 1
        message.ack()

    def run(self, *args, **kwargs):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        self.worker.on_start()
        super(AWXConsumer, self).run(*args, **kwargs)

    def stop(self, signum, frame):
        self.should_stop = True  # this makes the kombu mixin stop consuming
        logger.warn('received {}, stopping'.format(signame(signum)))
        self.worker.on_stop()
        raise SystemExit()


class BaseWorker(object):

    def work_loop(self, queue, finished, idx, *args):
        ppid = os.getppid()
        signal_handler = WorkerSignalHandler()
        while not signal_handler.kill_now:
            # if the parent PID changes, this process has been orphaned
            # via e.g., segfault or sigkill, we should exit too
            if os.getppid() != ppid:
                break
            try:
                body = queue.get(block=True, timeout=1)
                if body == 'QUIT':
                    break
            except QueueEmpty:
                continue
            except Exception as e:
                logger.error("Exception on worker {}, restarting: ".format(idx) + str(e))
                continue
            try:
                for conn in db.connections.all():
                    # If the database connection has a hiccup during the prior message, close it
                    # so we can establish a new connection
                    conn.close_if_unusable_or_obsolete()
                self.perform_work(body, *args)
            finally:
                if 'uuid' in body:
                    uuid = body['uuid']
                    logger.debug('task {} is finished'.format(uuid))
                    finished.put(uuid)
        logger.warn('worker exiting gracefully pid:{}'.format(os.getpid()))

    def perform_work(self, body):
        raise NotImplementedError()

    def on_start(self):
        pass

    def on_stop(self):
        pass
