# Copyright (c) 2018 Ansible by Red Hat
# All Rights Reserved.

import os
import logging
import signal
import sys
import redis
import json
import psycopg
import time
from uuid import UUID
from queue import Empty as QueueEmpty
from datetime import timedelta

from django import db
from django.conf import settings

from awx.main.dispatch.pool import WorkerPool
from awx.main.dispatch.periodic import Scheduler
from awx.main.dispatch import pg_bus_conn
from awx.main.utils.common import log_excess_runtime
from awx.main.utils.db import set_connection_name
import awx.main.analytics.subsystem_metrics as s_metrics

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
        self.redis = redis.Redis.from_url(settings.BROKER_URL)

    @property
    def listening_on(self):
        return f'listening on {self.queues}'

    def control(self, body):
        logger.warning(f'Received control signal:\n{body}')
        control = body.get('control')
        if control in ('status', 'schedule', 'running', 'cancel'):
            reply_queue = body['reply_to']
            if control == 'status':
                msg = '\n'.join([self.listening_on, self.pool.debug()])
            if control == 'schedule':
                msg = self.scheduler.debug()
            elif control == 'running':
                msg = []
                for worker in self.pool.workers:
                    worker.calculate_managed_tasks()
                    msg.extend(worker.managed_tasks.keys())
            elif control == 'cancel':
                msg = []
                task_ids = set(body['task_ids'])
                for worker in self.pool.workers:
                    task = worker.current_task
                    if task and task['uuid'] in task_ids:
                        logger.warn(f'Sending SIGTERM to task id={task["uuid"]}, task={task.get("task")}, args={task.get("args")}')
                        os.kill(worker.pid, signal.SIGTERM)
                        msg.append(task['uuid'])
                if task_ids and not msg:
                    logger.info(f'Could not locate running tasks to cancel with ids={task_ids}')

            with pg_bus_conn() as conn:
                conn.notify(reply_queue, json.dumps(msg))
        elif control == 'reload':
            for worker in self.pool.workers:
                worker.quit()
        else:
            logger.error('unrecognized control message: {}'.format(control))

    def dispatch_task(self, body):
        """This will place the given body into a worker queue to run method decorated as a task"""
        if isinstance(body, dict):
            body['time_ack'] = time.time()

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

    def process_task(self, body):
        """Routes the task details in body as either a control task or a task-task"""
        if 'control' in body:
            try:
                return self.control(body)
            except Exception:
                logger.exception(f"Exception handling control message: {body}")
                return
        self.dispatch_task(body)

    @log_excess_runtime(logger)
    def record_statistics(self):
        if time.time() - self.last_stats > 1:  # buffer stat recording to once per second
            try:
                self.redis.set(f'awx_{self.name}_statistics', self.pool.debug())
            except Exception:
                logger.exception(f"encountered an error communicating with redis to store {self.name} statistics")
            self.last_stats = time.time()

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


class AWXConsumerPG(AWXConsumerBase):
    def __init__(self, *args, schedule=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pg_max_wait = settings.DISPATCHER_DB_DOWNTIME_TOLERANCE
        # if no successful loops have ran since startup, then we should fail right away
        self.pg_is_down = True  # set so that we fail if we get database errors on startup
        init_time = time.time()
        self.pg_down_time = init_time - self.pg_max_wait  # allow no grace period
        self.last_cleanup = init_time
        self.subsystem_metrics = s_metrics.Metrics(auto_pipe_execute=False)
        self.last_metrics_gather = init_time
        self.listen_cumulative_time = 0.0
        if schedule:
            schedule = schedule.copy()
        else:
            schedule = {}
        # add control tasks to be ran at regular schedules
        # NOTE: if we run out of database connections, it is important to still run cleanup
        # so that we scale down workers and free up connections
        schedule['pool_cleanup'] = {'control': self.pool.cleanup, 'schedule': timedelta(seconds=60)}
        # record subsystem metrics for the dispatcher
        schedule['metrics_gather'] = {'control': self.record_metrics, 'schedule': timedelta(seconds=20)}
        self.scheduler = Scheduler(schedule)

    def record_metrics(self):
        current_time = time.time()
        self.pool.produce_subsystem_metrics(self.subsystem_metrics)
        self.subsystem_metrics.set('dispatcher_availability', self.listen_cumulative_time / (current_time - self.last_metrics_gather))
        self.subsystem_metrics.pipe_execute()
        self.listen_cumulative_time = 0.0
        self.last_metrics_gather = current_time

    def run_periodic_tasks(self):
        """
        Run general periodic logic, and return maximum time in seconds before
        the next requested run
        This may be called more often than that when events are consumed
        so this should be very efficient in that
        """
        try:
            self.record_statistics()  # maintains time buffer in method
        except Exception as exc:
            logger.warning(f'Failed to save dispatcher statistics {exc}')

        for job in self.scheduler.get_and_mark_pending():
            if 'control' in job.data:
                try:
                    job.data['control']()
                except Exception:
                    logger.exception(f'Error running control task {job.data}')
            elif 'task' in job.data:
                body = self.worker.resolve_callable(job.data['task']).get_async_body()
                # bypasses pg_notify for scheduled tasks
                self.dispatch_task(body)

        self.pg_is_down = False
        self.listen_start = time.time()

        return self.scheduler.time_until_next_run()

    def run(self, *args, **kwargs):
        super(AWXConsumerPG, self).run(*args, **kwargs)

        logger.info(f"Running worker {self.name} listening to queues {self.queues}")
        init = False

        while True:
            try:
                with pg_bus_conn(new_connection=True) as conn:
                    for queue in self.queues:
                        conn.listen(queue)
                    if init is False:
                        self.worker.on_start()
                        init = True
                    # run_periodic_tasks run scheduled actions and gives time until next scheduled action
                    # this is saved to the conn (PubSub) object in order to modify read timeout in-loop
                    conn.select_timeout = self.run_periodic_tasks()
                    # this is the main operational loop for awx-manage run_dispatcher
                    for e in conn.events(yield_timeouts=True):
                        self.listen_cumulative_time += time.time() - self.listen_start  # for metrics
                        if e is not None:
                            self.process_task(json.loads(e.payload))
                        conn.select_timeout = self.run_periodic_tasks()
                    if self.should_stop:
                        return
            except psycopg.InterfaceError:
                logger.warning("Stale Postgres message bus connection, reconnecting")
                continue
            except (db.DatabaseError, psycopg.OperationalError):
                # If we have attained stady state operation, tolerate short-term database hickups
                if not self.pg_is_down:
                    logger.exception(f"Error consuming new events from postgres, will retry for {self.pg_max_wait} s")
                    self.pg_down_time = time.time()
                    self.pg_is_down = True
                current_downtime = time.time() - self.pg_down_time
                if current_downtime > self.pg_max_wait:
                    logger.exception(f"Postgres event consumer has not recovered in {current_downtime} s, exiting")
                    raise
                # Wait for a second before next attempt, but still listen for any shutdown signals
                for i in range(10):
                    if self.should_stop:
                        return
                    time.sleep(0.1)
                for conn in db.connections.all():
                    conn.close_if_unusable_or_obsolete()
            except Exception:
                # Log unanticipated exception in addition to writing to stderr to get timestamps and other metadata
                logger.exception('Encountered unhandled error in dispatcher main loop')
                raise


class BaseWorker(object):
    def read(self, queue):
        return queue.get(block=True, timeout=1)

    def work_loop(self, queue, finished, idx, *args):
        ppid = os.getppid()
        signal_handler = WorkerSignalHandler()
        set_connection_name('worker')  # set application_name to distinguish from other dispatcher processes
        while not signal_handler.kill_now:
            # if the parent PID changes, this process has been orphaned
            # via e.g., segfault or sigkill, we should exit too
            if os.getppid() != ppid:
                break
            try:
                body = self.read(queue)
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
            finally:
                if 'uuid' in body:
                    uuid = body['uuid']
                    finished.put(uuid)
        logger.debug('worker exiting gracefully pid:{}'.format(os.getpid()))

    def perform_work(self, body):
        raise NotImplementedError()

    def on_start(self):
        pass

    def on_stop(self):
        pass
