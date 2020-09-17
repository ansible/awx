import logging
import os
import random
import signal
import sys
import time
import traceback
from datetime import datetime
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

from awx.main.models import UnifiedJob
from awx.main.dispatch import reaper

if 'run_callback_receiver' in sys.argv:
    logger = logging.getLogger('awx.main.commands.run_callback_receiver')
else:
    logger = logging.getLogger('awx.main.dispatch')


class NoOpResultQueue(object):

    def put(self, item):
        pass


class PoolWorker(object):
    '''
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
    '''

    track_managed_tasks = False

    def __init__(self, queue_size, target, args, **kwargs):
        self.messages_sent = 0
        self.messages_finished = 0
        self.managed_tasks = collections.OrderedDict()
        self.finished = MPQueue(queue_size) if self.track_managed_tasks else NoOpResultQueue()
        self.queue = MPQueue(queue_size)
        self.process = Process(target=target, args=(self.queue, self.finished) + args)
        self.process.daemon = True

    def start(self):
        self.process.start()

    def put(self, body):
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
        '''
        Send a special control message to the worker that tells it to exit
        gracefully.
        '''
        self.queue.put('QUIT')

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
            return '{:0.3f}'.format(
                psutil.Process(self.pid).memory_info().rss / 1024.0 / 1024.0
            )
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
                logger.warn('Event UUID {} appears to be have been duplicated.'.format(uuid))

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
                logger.error(
                    'requeuing {} messages from gone worker pid:{}'.format(
                        len(orphaned), self.pid
                    )
                )
        return orphaned

    @property
    def busy(self):
        self.calculate_managed_tasks()
        return len(self.managed_tasks) > 0

    @property
    def idle(self):
        return not self.busy


class StatefulPoolWorker(PoolWorker):

    track_managed_tasks = True


class WorkerPool(object):
    '''
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
    '''

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
            logger.warn('scaling up worker pid:{}'.format(worker.pid))
        return idx, worker

    def debug(self, *args, **kwargs):
        tmpl = Template(
            'Recorded at: {{ dt }} \n'
            '{{ pool.name }}[pid:{{ pool.pid }}] workers total={{ workers|length }} {{ meta }} \n'
            '{% for w in workers %}'
            '.  worker[pid:{{ w.pid }}]{% if not w.alive %} GONE exit={{ w.exitcode }}{% endif %}'
            ' sent={{ w.messages_sent }}'
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
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        return tmpl.render(
            pool=self, workers=self.workers, meta=self.debug_meta,
            dt=now
        )

    def write(self, preferred_queue, body):
        queue_order = sorted(range(len(self.workers)), key=lambda x: -1 if x==preferred_queue else x)
        write_attempt_order = []
        for queue_actual in queue_order:
            try:
                self.workers[queue_actual].put(body)
                return queue_actual
            except QueueFull:
                pass
            except Exception:
                tb = traceback.format_exc()
                logger.warn("could not write to queue %s" % preferred_queue)
                logger.warn("detail: {}".format(tb))
            write_attempt_order.append(preferred_queue)
        logger.error("could not write payload to any queue, attempted order: {}".format(write_attempt_order))
        return None

    def stop(self, signum):
        try:
            for worker in self.workers:
                os.kill(worker.pid, signum)
        except Exception:
            logger.exception('could not kill {}'.format(worker.pid))


class AutoscalePool(WorkerPool):
    '''
    An extended pool implementation that automatically scales workers up and
    down based on demand
    '''

    pool_cls = StatefulPoolWorker

    def __init__(self, *args, **kwargs):
        self.max_workers = kwargs.pop('max_workers', None)
        super(AutoscalePool, self).__init__(*args, **kwargs)

        if self.max_workers is None:
            settings_absmem = getattr(settings, 'SYSTEM_TASK_ABS_MEM', None)
            if settings_absmem is not None:
                total_memory_gb = int(settings_absmem)
            else:
                total_memory_gb = (psutil.virtual_memory().total >> 30) + 1  # noqa: round up
            # 5 workers per GB of total memory
            self.max_workers = (total_memory_gb * 5)

        # max workers can't be less than min_workers
        self.max_workers = max(self.min_workers, self.max_workers)

    def debug(self, *args, **kwargs):
        self.cleanup()
        return super(AutoscalePool, self).debug(*args, **kwargs)

    @property
    def should_grow(self):
        if len(self.workers) < self.min_workers:
            # If we don't have at least min_workers, add more
            return True
        # If every worker is busy doing something, add more
        return all([w.busy for w in self.workers])

    @property
    def full(self):
        return len(self.workers) == self.max_workers

    @property
    def debug_meta(self):
        return 'min={} max={}'.format(self.min_workers, self.max_workers)

    def cleanup(self):
        """
        Perform some internal account and cleanup.  This is run on
        every cluster node heartbeat:

        1.  Discover worker processes that exited, and recover messages they
            were handling.
        2.  Clean up unnecessary, idle workers.
        3.  Check to see if the database says this node is running any tasks
            that aren't actually running.  If so, reap them.

        IMPORTANT: this function is one of the few places in the dispatcher
        (aside from setting lookups) where we talk to the database.  As such,
        if there's an outage, this method _can_ throw various
        django.db.utils.Error exceptions.  Act accordingly.
        """
        orphaned = []
        for w in self.workers[::]:
            if not w.alive:
                # the worker process has exited
                # 1. take the task it was running and enqueue the error
                #    callbacks
                # 2. take any pending tasks delivered to its queue and
                #    send them to another worker
                logger.error('worker pid:{} is gone (exit={})'.format(w.pid, w.exitcode))
                if w.current_task:
                    if w.current_task != 'QUIT':
                        try:
                            for j in UnifiedJob.objects.filter(celery_task_id=w.current_task['uuid']):
                                reaper.reap_job(j, 'failed')
                        except Exception:
                            logger.exception('failed to reap job UUID {}'.format(w.current_task['uuid']))
                orphaned.extend(w.orphaned_tasks)
                self.workers.remove(w)
            elif w.idle and len(self.workers) > self.min_workers:
                # the process has an empty queue (it's idle) and we have
                # more processes in the pool than we need (> min)
                # send this process a message so it will exit gracefully
                # at the next opportunity
                logger.warn('scaling down worker pid:{}'.format(w.pid))
                w.quit()
                self.workers.remove(w)
            if w.alive:
                # if we discover a task manager invocation that's been running
                # too long, reap it (because otherwise it'll just hold the postgres
                # advisory lock forever); the goal of this code is to discover
                # deadlocks or other serious issues in the task manager that cause
                # the task manager to never do more work
                current_task = w.current_task
                if current_task and isinstance(current_task, dict):
                    if current_task.get('task', '').endswith('tasks.run_task_manager'):
                        if 'started' not in current_task:
                            w.managed_tasks[
                                current_task['uuid']
                            ]['started'] = time.time()
                        age = time.time() - current_task['started']
                        w.managed_tasks[current_task['uuid']]['age'] = age
                        if age > (60 * 5):
                            logger.error(
                                f'run_task_manager has held the advisory lock for >5m, sending SIGTERM to {w.pid}'
                            )  # noqa
                            os.kill(w.pid, signal.SIGTERM)

        for m in orphaned:
            # if all the workers are dead, spawn at least one
            if not len(self.workers):
                self.up()
            idx = random.choice(range(len(self.workers)))
            self.write(idx, m)

        # if the database says a job is running on this node, but it's *not*,
        # then reap it
        running_uuids = []
        for worker in self.workers:
            worker.calculate_managed_tasks()
            running_uuids.extend(list(worker.managed_tasks.keys()))
        reaper.reap(excluded_uuids=running_uuids)

    def up(self):
        if self.full:
            # if we can't spawn more workers, just toss this message into a
            # random worker's backlog
            idx = random.choice(range(len(self.workers)))
            return idx, self.workers[idx]
        else:
            return super(AutoscalePool, self).up()

    def write(self, preferred_queue, body):
        try:
            # when the cluster heartbeat occurs, clean up internally
            if isinstance(body, dict) and 'cluster_node_heartbeat' in body['task']:
                self.cleanup()
            if self.should_grow:
                self.up()
            # we don't care about "preferred queue" round robin distribution, just
            # find the first non-busy worker and claim it
            workers = self.workers[:]
            random.shuffle(workers)
            for w in workers:
                if not w.busy:
                    w.put(body)
                    break
            else:
                return super(AutoscalePool, self).write(preferred_queue, body)
        except Exception:
            for conn in connections.all():
                # If the database connection has a hiccup, re-establish a new
                # connection
                conn.close_if_unusable_or_obsolete()
            logger.exception('failed to write inbound message')
