# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

from kombu import Connection, Exchange, Queue
from kombu.mixins import ConsumerMixin

# Django
from django.conf import settings
from django.core.management.base import NoArgsCommand
from django.db import DatabaseError

# AWX
from awx.main.models import * # noqa

logger = logging.getLogger('awx.main.commands.run_callback_receiver')


class CallbackBrokerWorker(ConsumerMixin):
    def __init__(self, connection):
        self.connection = connection

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=[Queue(settings.CALLBACK_QUEUE,
                                       Exchange(settings.CALLBACK_QUEUE, type='direct'),
                                       routing_key=settings.CALLBACK_QUEUE)],
                         accept=['json'],
                         callbacks=[self.process_task])]

    def process_task(self, body, message):
        try:
            if 'event' not in body:
                raise Exception('Payload does not have an event')
            if 'job_id' not in body and 'ad_hoc_command_id' not in body:
                raise Exception('Payload does not have a job_id or ad_hoc_command_id')
            if settings.DEBUG:
                logger.info('Body: {}'.format(body))
                logger.info('Message: {}'.format(message))
            try:
                if 'job_id' in body:
                    JobEvent.create_from_data(**body)
                elif 'ad_hoc_command_id' in body:
                    AdHocCommandEvent.create_from_data(**body)
            except DatabaseError as e:
                logger.error('Database Error Saving Job Event: {}'.format(e))
        except Exception as exc:
            import traceback
            traceback.print_exc()
            logger.error('Callback Task Processor Raised Exception: %r', exc)
        message.ack()


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
