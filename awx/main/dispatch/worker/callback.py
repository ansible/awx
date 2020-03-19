import cProfile
import logging
import os
import pstats
import signal
import tempfile
import time
import traceback
from queue import Empty as QueueEmpty

from django.conf import settings
from django.utils.timezone import now as tz_now
from django.db import DatabaseError, OperationalError, connection as django_connection
from django.db.utils import InterfaceError, InternalError, IntegrityError

from awx.main.consumers import emit_channel_notification
from awx.main.models import (JobEvent, AdHocCommandEvent, ProjectUpdateEvent,
                             InventoryUpdateEvent, SystemJobEvent, UnifiedJob,
                             Job)
from awx.main.tasks import handle_success_and_failure_notifications
from awx.main.models.events import emit_event_detail

from .base import BaseWorker

logger = logging.getLogger('awx.main.commands.run_callback_receiver')

# the number of seconds to buffer events in memory before flushing
# using JobEvent.objects.bulk_create()
BUFFER_SECONDS = .1


class CallbackBrokerWorker(BaseWorker):
    '''
    A worker implementation that deserializes callback event data and persists
    it into the database.

    The code that *generates* these types of messages is found in the
    ansible-runner display callback plugin.
    '''

    MAX_RETRIES = 2
    prof = None

    def __init__(self):
        self.buff = {}

    def read(self, queue):
        try:
            return queue.get(block=True, timeout=BUFFER_SECONDS)
        except QueueEmpty:
            return {'event': 'FLUSH'}

    def toggle_profiling(self, *args):
        if self.prof:
            self.prof.disable()
            filename = f'callback-{os.getpid()}.pstats'
            filepath = os.path.join(tempfile.gettempdir(), filename)
            with open(filepath, 'w') as f:
                pstats.Stats(self.prof, stream=f).sort_stats('cumulative').print_stats()
            pstats.Stats(self.prof).dump_stats(filepath + '.raw')
            self.prof = False
            logger.error(f'profiling is disabled, wrote {filepath}')
        else:
            self.prof = cProfile.Profile()
            self.prof.enable()
            logger.error('profiling is enabled')

    def work_loop(self, *args, **kw):
        if settings.AWX_CALLBACK_PROFILE:
            signal.signal(signal.SIGUSR1, self.toggle_profiling)
        return super(CallbackBrokerWorker, self).work_loop(*args, **kw)

    def flush(self, force=False):
        now = tz_now()
        if (
            force or
            any([len(events) >= 1000 for events in self.buff.values()])
        ):
            for cls, events in self.buff.items():
                logger.debug(f'{cls.__name__}.objects.bulk_create({len(events)})')
                for e in events:
                    if not e.created:
                        e.created = now
                    e.modified = now
                try:
                    cls.objects.bulk_create(events)
                except Exception as exc:
                    # if an exception occurs, we should re-attempt to save the
                    # events one-by-one, because something in the list is
                    # broken/stale (e.g., an IntegrityError on a specific event)
                    for e in events:
                        try:
                            if (
                                isinstance(exc, IntegrityError),
                                getattr(e, 'host_id', '')
                            ):
                                # this is one potential IntegrityError we can
                                # work around - if the host disappears before
                                # the event can be processed
                                e.host_id = None
                            e.save()
                        except Exception:
                            logger.exception('Database Error Saving Job Event')
                for e in events:
                    emit_event_detail(e)
            self.buff = {}

    def perform_work(self, body):
        try:
            flush = body.get('event') == 'FLUSH'
            if not flush:
                event_map = {
                    'job_id': JobEvent,
                    'ad_hoc_command_id': AdHocCommandEvent,
                    'project_update_id': ProjectUpdateEvent,
                    'inventory_update_id': InventoryUpdateEvent,
                    'system_job_id': SystemJobEvent,
                }

                job_identifier = 'unknown job'
                for key, cls in event_map.items():
                    if key in body:
                        job_identifier = body[key]
                        break

                if body.get('event') == 'EOF':
                    try:
                        final_counter = body.get('final_counter', 0)
                        logger.info('Event processing is finished for Job {}, sending notifications'.format(job_identifier))
                        # EOF events are sent when stdout for the running task is
                        # closed. don't actually persist them to the database; we
                        # just use them to report `summary` websocket events as an
                        # approximation for when a job is "done"
                        emit_channel_notification(
                            'jobs-summary',
                            dict(group_name='jobs', unified_job_id=job_identifier, final_counter=final_counter)
                        )
                        # Additionally, when we've processed all events, we should
                        # have all the data we need to send out success/failure
                        # notification templates
                        uj = UnifiedJob.objects.get(pk=job_identifier)

                        if isinstance(uj, Job):
                            # *actual playbooks* send their success/failure
                            # notifications in response to the playbook_on_stats
                            # event handling code in main.models.events
                            pass
                        elif hasattr(uj, 'send_notification_templates'):
                            handle_success_and_failure_notifications.apply_async([uj.id])
                    except Exception:
                        logger.exception('Worker failed to emit notifications: Job {}'.format(job_identifier))
                    return

                event = cls.create_from_data(**body)
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
                    logger.exception('Database Error Saving Job Event, retry #{i} in {delay} seconds:'.format(
                        i=retries + 1,
                        delay=delay
                    ))
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
