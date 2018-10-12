import logging
import time
import os
import signal
import traceback

from django.conf import settings
from django.db import DatabaseError, OperationalError, connection as django_connection
from django.db.utils import InterfaceError, InternalError

from awx.main.consumers import emit_channel_notification
from awx.main.models import (JobEvent, AdHocCommandEvent, ProjectUpdateEvent,
                             InventoryUpdateEvent, SystemJobEvent, UnifiedJob)

from .base import BaseWorker

logger = logging.getLogger('awx.main.dispatch')


class CallbackBrokerWorker(BaseWorker):
    '''
    A worker implementation that deserializes callback event data and persists
    it into the database.

    The code that *builds* these types of messages is found in the AWX display
    callback (`awx.lib.awx_display_callback`).
    '''

    MAX_RETRIES = 2

    def perform_work(self, body):
        try:
            event_map = {
                'job_id': JobEvent,
                'ad_hoc_command_id': AdHocCommandEvent,
                'project_update_id': ProjectUpdateEvent,
                'inventory_update_id': InventoryUpdateEvent,
                'system_job_id': SystemJobEvent,
            }

            if not any([key in body for key in event_map]):
                raise Exception('Payload does not have a job identifier')
            if settings.DEBUG:
                from pygments import highlight
                from pygments.lexers import PythonLexer
                from pygments.formatters import Terminal256Formatter
                from pprint import pformat
                logger.info('Body: {}'.format(
                    highlight(pformat(body, width=160), PythonLexer(), Terminal256Formatter(style='friendly'))
                )[:1024 * 4])

            def _save_event_data():
                for key, cls in event_map.items():
                    if key in body:
                        cls.create_from_data(**body)

            job_identifier = 'unknown job'
            for key in event_map.keys():
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
                    if hasattr(uj, 'send_notification_templates'):
                        retries = 0
                        while retries < 5:
                            if uj.finished:
                                uj.send_notification_templates('succeeded' if uj.status == 'successful' else 'failed')
                                break
                            else:
                                # wait a few seconds to avoid a race where the
                                # events are persisted _before_ the UJ.status
                                # changes from running -> successful
                                retries += 1
                                time.sleep(1)
                                uj = UnifiedJob.objects.get(pk=job_identifier)
                except Exception:
                    logger.exception('Worker failed to emit notifications: Job {}'.format(job_identifier))
                return

            retries = 0
            while retries <= self.MAX_RETRIES:
                try:
                    _save_event_data()
                    break
                except (OperationalError, InterfaceError, InternalError):
                    if retries >= self.MAX_RETRIES:
                        logger.exception('Worker could not re-establish database connectivity, shutting down gracefully: Job {}'.format(job_identifier))
                        os.kill(os.getppid(), signal.SIGINT)
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
                    logger.exception('Database Error Saving Job Event for Job {}'.format(job_identifier))
                    break
        except Exception as exc:
            tb = traceback.format_exc()
            logger.error('Callback Task Processor Raised Exception: %r', exc)
            logger.error('Detail: {}'.format(tb))
