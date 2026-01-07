import logging
import os
import sys
import time
import traceback
from datetime import datetime, timezone
from uuid import uuid4

import collections
from multiprocessing import Process
from multiprocessing import Queue as MPQueue
from queue import Full as QueueFull, Empty as QueueEmpty

from django.conf import settings
from django.db import connection as django_connection, connections
from django.core.cache import cache as django_cache
from jinja2 import Template
import psutil


if 'run_callback_receiver' in sys.argv:
    logger = logging.getLogger('awx.main.commands.run_callback_receiver')
else:
    logger = logging.getLogger('awx.main.dispatch')


class NoOpResultQueue(object):
    def put(self, item):
        pass


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

    track_managed_tasks = False

    def __init__(self, queue_size, target, args, **kwargs):
        self.messages_sent = 0
        self.messages_finished = 0
        self.managed_tasks = collections.OrderedDict()
        self.finished = MPQueue(queue_size) if self.track_managed_tasks else NoOpResultQueue()
        self.queue = MPQueue(queue_size)
        self.process = Process(target=target, args=(self.queue, self.finished) + args)
        self.process.daemon = True
        self.creation_time = time.monotonic()
        self.retiring = False

    def start(self):
        self.process.start()

    def put(self, body):
        if self.retiring:
            uuid = body.get('uuid', 'N/A') if isinstance(body, dict) else 'N/A'
            logger.info(f"Worker pid:{self.pid} is retiring. Refusing new task {uuid}.")
            raise QueueFull("Worker is retiring and not accepting new tasks")
        uuid = '?'
        if isinstance(body, dict):
            if not body.get('uuid'):
                body['uuid'] = str(uuid4())
            uuid = body['uuid']
        if self.track_managed_tasks:
            self.managed_tasks[uuid] = body
        self.queue.put(body, block=True, timeout=5)
        self.messages_sent += 1
        self.calculate_managed_tasks()

    def quit(self):
        """
        Send a special control message to the worker that tells it to exit
        gracefully.
        """
        self.queue.put('QUIT')

    @property
    def age(self):
        """Returns the current age of the worker in seconds."""
        return time.monotonic() - self.creation_time

    @property
    def pid(self):
        return self.process.pid

    @property
    def qsize(self):
        return self.queue.qsize()

    @property
    def alive(self):
        return self.process.is_alive()

    @property
    def mb(self):
        if self.alive:
            return '{:0.3f}'.format(psutil.Process(self.pid).memory_info().rss / 1024.0 / 1024.0)
        return '0'

    @property
    def exitcode(self):
        return str(self.process.exitcode)

    def calculate_managed_tasks(self):
        if not self.track_managed_tasks:
            return
        # look to see if any tasks were finished
        finished = []
        for _ in range(self.finished.qsize()):
            try:
                finished.append(self.finished.get(block=False))
            except QueueEmpty:
                break  # qsize is not always _totally_ up to date

        # if any tasks were finished, removed them from the managed tasks for
        # this worker
        for uuid in finished:
            try:
                del self.managed_tasks[uuid]
                self.messages_finished += 1
            except KeyError:
                # ansible _sometimes_ appears to send events w/ duplicate UUIDs;
                # UUIDs for ansible events are *not* actually globally unique
                # when this occurs, it's _fine_ to ignore this KeyError because
                # the purpose of self.managed_tasks is to just track internal
                # state of which events are *currently* being processed.
                logger.warning('Event UUID {} appears to be have been duplicated.'.format(uuid))

    @property
    def current_task(self):
        if not self.track_managed_tasks:
            return None
        self.calculate_managed_tasks()
        # the task at [0] is the one that's running right now (or is about to
        # be running)
        if len(self.managed_tasks):
            return self.managed_tasks[list(self.managed_tasks.keys())[0]]

        return None

    @property
    def orphaned_tasks(self):
        if not self.track_managed_tasks:
            return []
        orphaned = []
        if not self.alive:
            # if this process had a running task that never finished,
            # requeue its error callbacks
            current_task = self.current_task
            if isinstance(current_task, dict):
                orphaned.extend(current_task.get('errbacks', []))

            # if this process has any pending messages requeue them
            for _ in range(self.qsize):
                try:
                    message = self.queue.get(block=False)
                    if message != 'QUIT':
                        orphaned.append(message)
                except QueueEmpty:
                    break  # qsize is not always _totally_ up to date
            if len(orphaned):
                logger.error('requeuing {} messages from gone worker pid:{}'.format(len(orphaned), self.pid))
        return orphaned

    @property
    def busy(self):
        self.calculate_managed_tasks()
        return len(self.managed_tasks) > 0

    @property
    def idle(self):
        return not self.busy


class WorkerPool(object):
    """
    Creates a pool of forked PoolWorkers.

    As WorkerPool.write(...) is called (generally, by a kombu consumer
    implementation when it receives an AMQP message), messages are passed to
    one of the multiprocessing Queues where some work can be done on them.

    class MessagePrinter(awx.main.dispatch.worker.BaseWorker):

        def perform_work(self, body):
            print(body)

    pool = WorkerPool(min_workers=4)  # spawn four worker processes
    pool.init_workers(MessagePrint().work_loop)
    pool.write(
        0,  # preferred worker 0
        'Hello, World!'
    )
    """

    pool_cls = PoolWorker
    debug_meta = ''

    def __init__(self, min_workers=None, queue_size=None):
        self.name = settings.CLUSTER_HOST_ID
        self.pid = os.getpid()
        self.min_workers = min_workers or settings.JOB_EVENT_WORKERS
        self.queue_size = queue_size or settings.JOB_EVENT_MAX_QUEUE_SIZE
        self.workers = []

    def __len__(self):
        return len(self.workers)

    def init_workers(self, target, *target_args):
        self.target = target
        self.target_args = target_args
        for idx in range(self.min_workers):
            self.up()

    def up(self):
        idx = len(self.workers)
        # It's important to close these because we're _about_ to fork, and we
        # don't want the forked processes to inherit the open sockets
        # for the DB and cache connections (that way lies race conditions)
        django_connection.close()
        django_cache.close()
        worker = self.pool_cls(self.queue_size, self.target, (idx,) + self.target_args)
        self.workers.append(worker)
        try:
            worker.start()
        except Exception:
            logger.exception('could not fork')
        else:
            logger.debug('scaling up worker pid:{}'.format(worker.pid))
        return idx, worker

    def debug(self, *args, **kwargs):
        tmpl = Template(
            'Recorded at: {{ dt }} \n'
            '{{ pool.name }}[pid:{{ pool.pid }}] workers total={{ workers|length }} {{ meta }} \n'
            '{% for w in workers %}'
            '.  worker[pid:{{ w.pid }}]{% if not w.alive %} GONE exit={{ w.exitcode }}{% endif %}'
            ' sent={{ w.messages_sent }}'
            ' age={{ "%.0f"|format(w.age) }}s'
            ' retiring={{ w.retiring }}'
            '{% if w.messages_finished %} finished={{ w.messages_finished }}{% endif %}'
            ' qsize={{ w.managed_tasks|length }}'
            ' rss={{ w.mb }}MB'
            '{% for task in w.managed_tasks.values() %}'
            '\n     - {% if loop.index0 == 0 %}running {% if "age" in task %}for: {{ "%.1f" % task["age"] }}s {% endif %}{% else %}queued {% endif %}'
            '{{ task["uuid"] }} '
            '{% if "task" in task %}'
            '{{ task["task"].rsplit(".", 1)[-1] }}'
            # don't print kwargs, they often contain launch-time secrets
            '(*{{ task.get("args", []) }})'
            '{% endif %}'
            '{% endfor %}'
            '{% if not w.managed_tasks|length %}'
            ' [IDLE]'
            '{% endif %}'
            '\n'
            '{% endfor %}'
        )
        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        return tmpl.render(pool=self, workers=self.workers, meta=self.debug_meta, dt=now)

    def write(self, preferred_queue, body):
        queue_order = sorted(range(len(self.workers)), key=lambda x: -1 if x == preferred_queue else x)
        write_attempt_order = []
        for queue_actual in queue_order:
            try:
                self.workers[queue_actual].put(body)
                return queue_actual
            except QueueFull:
                pass
            except Exception:
                tb = traceback.format_exc()
                logger.warning("could not write to queue %s" % preferred_queue)
                logger.warning("detail: {}".format(tb))
            write_attempt_order.append(preferred_queue)
        logger.error("could not write payload to any queue, attempted order: {}".format(write_attempt_order))
        return None

    def stop(self, signum):
        try:
            for worker in self.workers:
                os.kill(worker.pid, signum)
        except Exception:
            logger.exception('could not kill {}'.format(worker.pid))
