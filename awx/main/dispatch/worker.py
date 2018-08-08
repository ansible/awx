# Copyright (c) 2018 Ansible by Red Hat
# All Rights Reserved.

import logging
import os
import signal
import time
import traceback
from uuid import UUID
from Queue import Empty as QueueEmpty

from kombu.mixins import ConsumerMixin
from django.conf import settings
from django.db import DatabaseError, OperationalError, connection as django_connection
from django.db.utils import InterfaceError, InternalError

from awx.main.models import (JobEvent, AdHocCommandEvent, ProjectUpdateEvent,
                             InventoryUpdateEvent, SystemJobEvent, UnifiedJob)
from awx.main.consumers import emit_channel_notification
from awx.main.dispatch.pool import WorkerPool

logger = logging.getLogger('awx.main.dispatch')


class WorkerSignalHandler:

    def __init__(self):
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, *args, **kwargs):
        self.kill_now = True


class AWXConsumer(ConsumerMixin):

    def __init__(self, connection, worker, queues=[]):
        self.connection = connection
        self.total_messages = 0
        self.queues = queues
        self.pool = WorkerPool()
        self.pool.init_workers(worker.work_loop)

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=self.queues, accept=['json'],
                         callbacks=[self.process_task])]

    def process_task(self, body, message):
        if "uuid" in body and body['uuid']:
            try:
                queue = UUID(body['uuid']).int % len(self.pool)
            except Exception:
                queue = self.total_messages % len(self.pool)
        else:
            queue = self.total_messages % len(self.pool)
        self.pool.write(queue, body)
        self.total_messages += 1
        message.ack()


class BaseWorker(object):

    def work_loop(self, queue, idx, *args):
        signal_handler = WorkerSignalHandler()
        while not signal_handler.kill_now:
            try:
                body = queue.get(block=True, timeout=1)
            except QueueEmpty:
                continue
            except Exception as e:
                logger.error("Exception on worker, restarting: " + str(e))
                continue
            self.perform_work(body, *args)

    def perform_work(self, body):
        raise NotImplemented()


class CallbackBrokerWorker(BaseWorker):

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
                except (OperationalError, InterfaceError, InternalError) as e:
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
                except DatabaseError as e:
                    logger.exception('Database Error Saving Job Event for Job {}'.format(job_identifier))
                    break
        except Exception as exc:
            tb = traceback.format_exc()
            logger.error('Callback Task Processor Raised Exception: %r', exc)
            logger.error('Detail: {}'.format(tb))
