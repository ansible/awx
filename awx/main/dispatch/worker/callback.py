import json
import logging
import os
import signal
import time
import traceback

from django.conf import settings
from django.utils.functional import cached_property
from django.utils.timezone import now as tz_now
from django.db import DatabaseError, OperationalError, transaction, connection as django_connection
from django.db.utils import InterfaceError, InternalError
from django_guid import set_guid

import psutil

import redis

from awx.main.consumers import emit_channel_notification
from awx.main.models import JobEvent, AdHocCommandEvent, ProjectUpdateEvent, InventoryUpdateEvent, SystemJobEvent, UnifiedJob
from awx.main.constants import ACTIVE_STATES
from awx.main.models.events import emit_event_detail
from awx.main.utils.profiling import AWXProfiler
import awx.main.analytics.subsystem_metrics as s_metrics
from .base import BaseWorker

logger = logging.getLogger('awx.main.commands.run_callback_receiver')


def job_stats_wrapup(job_identifier, event=None):
    """Fill in the unified job host_status_counts, fire off notifications if needed"""
    try:
        # empty dict (versus default of None) can still indicate that events have been processed
        # for job types like system jobs, and jobs with no hosts matched
        host_status_counts = {}
        if event:
            host_status_counts = event.get_host_status_counts()

        # Update host_status_counts while holding the row lock
        with transaction.atomic():
            uj = UnifiedJob.objects.select_for_update().get(pk=job_identifier)
            uj.host_status_counts = host_status_counts
            uj.save(update_fields=['host_status_counts'])

        uj.log_lifecycle("stats_wrapup_finished")

        # If the status was a finished state before this update was made, send notifications
        # If not, we will send notifications when the status changes
        if uj.status not in ACTIVE_STATES:
            uj.send_notification_templates('succeeded' if uj.status == 'successful' else 'failed')

    except Exception:
        logger.exception('Worker failed to save stats or emit notifications: Job {}'.format(job_identifier))


class CallbackBrokerWorker(BaseWorker):
    """
    A worker implementation that deserializes callback event data and persists
    it into the database.

    The code that *generates* these types of messages is found in the
    ansible-runner display callback plugin.
    """

    MAX_RETRIES = 2
    last_stats = time.time()
    last_flush = time.time()
    total = 0
    last_event = ''
    prof = None

    def __init__(self):
        self.buff = {}
        self.redis = redis.Redis.from_url(settings.BROKER_URL)
        self.subsystem_metrics = s_metrics.Metrics(auto_pipe_execute=False)
        self.queue_pop = 0
        self.queue_name = settings.CALLBACK_QUEUE
        self.prof = AWXProfiler("CallbackBrokerWorker")
        for key in self.redis.keys('awx_callback_receiver_statistics_*'):
            self.redis.delete(key)

    @cached_property
    def pid(self):
        """This needs to be obtained after forking, or else it will give the parent process"""
        return os.getpid()

    def read(self, queue):
        try:
            res = self.redis.blpop(self.queue_name, timeout=1)
            if res is None:
                return {'event': 'FLUSH'}
            self.total += 1
            self.queue_pop += 1
            self.subsystem_metrics.inc('callback_receiver_events_popped_redis', 1)
            self.subsystem_metrics.inc('callback_receiver_events_in_memory', 1)
            return json.loads(res[1])
        except redis.exceptions.RedisError:
            logger.exception("encountered an error communicating with redis")
            time.sleep(1)
        except (json.JSONDecodeError, KeyError):
            logger.exception("failed to decode JSON message from redis")
        finally:
            self.record_statistics()
            self.record_read_metrics()

        return {'event': 'FLUSH'}

    def record_read_metrics(self):
        if self.queue_pop == 0:
            return
        if self.subsystem_metrics.should_pipe_execute() is True:
            queue_size = self.redis.llen(self.queue_name)
            self.subsystem_metrics.set('callback_receiver_events_queue_size_redis', queue_size)
            self.subsystem_metrics.pipe_execute()
            self.queue_pop = 0

    def record_statistics(self):
        # buffer stat recording to once per (by default) 5s
        if time.time() - self.last_stats > settings.JOB_EVENT_STATISTICS_INTERVAL:
            try:
                self.redis.set(f'awx_callback_receiver_statistics_{self.pid}', self.debug())
                self.last_stats = time.time()
            except Exception:
                logger.exception("encountered an error communicating with redis")
                self.last_stats = time.time()

    def debug(self):
        return f'.  worker[pid:{self.pid}] sent={self.total} rss={self.mb}MB {self.last_event}'

    @property
    def mb(self):
        return '{:0.3f}'.format(psutil.Process(self.pid).memory_info().rss / 1024.0 / 1024.0)

    def toggle_profiling(self, *args):
        if not self.prof.is_started():
            self.prof.start()
            logger.error('profiling is enabled')
        else:
            filepath = self.prof.stop()
            logger.error(f'profiling is disabled, wrote {filepath}')

    def work_loop(self, *args, **kw):
        if settings.AWX_CALLBACK_PROFILE:
            signal.signal(signal.SIGUSR1, self.toggle_profiling)
        return super(CallbackBrokerWorker, self).work_loop(*args, **kw)

    def flush(self, force=False):
        now = tz_now()
        if force or (time.time() - self.last_flush) > settings.JOB_EVENT_BUFFER_SECONDS or any([len(events) >= 1000 for events in self.buff.values()]):
            metrics_bulk_events_saved = 0
            metrics_singular_events_saved = 0
            metrics_events_batch_save_errors = 0
            metrics_events_broadcast = 0
            for cls, events in self.buff.items():
                logger.debug(f'{cls.__name__}.objects.bulk_create({len(events)})')
                for e in events:
                    if not e.created:
                        e.created = now
                    e.modified = now
                metrics_duration_to_save = time.perf_counter()
                try:
                    cls.objects.bulk_create(events)
                    metrics_bulk_events_saved += len(events)
                except Exception:
                    # if an exception occurs, we should re-attempt to save the
                    # events one-by-one, because something in the list is
                    # broken/stale
                    metrics_events_batch_save_errors += 1
                    for e in events:
                        try:
                            e.save()
                            metrics_singular_events_saved += 1
                        except Exception:
                            logger.exception('Database Error Saving Job Event')
                metrics_duration_to_save = time.perf_counter() - metrics_duration_to_save
                for e in events:
                    if not getattr(e, '_skip_websocket_message', False):
                        metrics_events_broadcast += 1
                        emit_event_detail(e)
                    if getattr(e, '_notification_trigger_event', False):
                        job_stats_wrapup(getattr(e, e.JOB_REFERENCE), event=e)
            self.buff = {}
            self.last_flush = time.time()
            # only update metrics if we saved events
            if (metrics_bulk_events_saved + metrics_singular_events_saved) > 0:
                self.subsystem_metrics.inc('callback_receiver_batch_events_errors', metrics_events_batch_save_errors)
                self.subsystem_metrics.inc('callback_receiver_events_insert_db_seconds', metrics_duration_to_save)
                self.subsystem_metrics.inc('callback_receiver_events_insert_db', metrics_bulk_events_saved + metrics_singular_events_saved)
                self.subsystem_metrics.observe('callback_receiver_batch_events_insert_db', metrics_bulk_events_saved)
                self.subsystem_metrics.inc('callback_receiver_events_in_memory', -(metrics_bulk_events_saved + metrics_singular_events_saved))
                self.subsystem_metrics.inc('callback_receiver_events_broadcast', metrics_events_broadcast)
            if self.subsystem_metrics.should_pipe_execute() is True:
                self.subsystem_metrics.pipe_execute()

    def perform_work(self, body):
        try:
            flush = body.get('event') == 'FLUSH'
            if flush:
                self.last_event = ''
            if not flush:
                job_identifier = 'unknown job'
                for cls in (JobEvent, AdHocCommandEvent, ProjectUpdateEvent, InventoryUpdateEvent, SystemJobEvent):
                    if cls.JOB_REFERENCE in body:
                        job_identifier = body[cls.JOB_REFERENCE]
                        break

                self.last_event = f'\n\t- {cls.__name__} for #{job_identifier} ({body.get("event", "")} {body.get("uuid", "")})'  # noqa

                notification_trigger_event = bool(body.get('event') == cls.WRAPUP_EVENT)

                if body.get('event') == 'EOF':
                    try:
                        if 'guid' in body:
                            set_guid(body['guid'])
                        final_counter = body.get('final_counter', 0)
                        logger.info('Starting EOF event processing for Job {}'.format(job_identifier))
                        # EOF events are sent when stdout for the running task is
                        # closed. don't actually persist them to the database; we
                        # just use them to report `summary` websocket events as an
                        # approximation for when a job is "done"
                        emit_channel_notification('jobs-summary', dict(group_name='jobs', unified_job_id=job_identifier, final_counter=final_counter))

                        if notification_trigger_event:
                            job_stats_wrapup(job_identifier)
                    except Exception:
                        logger.exception('Worker failed to perform EOF tasks: Job {}'.format(job_identifier))
                    finally:
                        self.subsystem_metrics.inc('callback_receiver_events_in_memory', -1)
                        set_guid('')
                    return

                skip_websocket_message = body.pop('skip_websocket_message', False)

                event = cls.create_from_data(**body)

                if skip_websocket_message:  # if this event sends websocket messages, fire them off on flush
                    event._skip_websocket_message = True

                if notification_trigger_event:  # if this is an Ansible stats event, ensure notifications on flush
                    event._notification_trigger_event = True

                self.buff.setdefault(cls, []).append(event)

            retries = 0
            while retries <= self.MAX_RETRIES:
                try:
                    self.flush(force=flush)
                    break
                except (OperationalError, InterfaceError, InternalError):
                    if retries >= self.MAX_RETRIES:
                        logger.exception('Worker could not re-establish database connectivity, giving up on one or more events.')
                        return
                    delay = 60 * retries
                    logger.exception('Database Error Saving Job Event, retry #{i} in {delay} seconds:'.format(i=retries + 1, delay=delay))
                    django_connection.close()
                    time.sleep(delay)
                    retries += 1
                except DatabaseError:
                    logger.exception('Database Error Saving Job Event')
                    break
        except Exception as exc:
            tb = traceback.format_exc()
            logger.error('Callback Task Processor Raised Exception: %r', exc)
            logger.error('Detail: {}'.format(tb))
