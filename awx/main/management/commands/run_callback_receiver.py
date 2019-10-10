# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.conf import settings
from django.core.management.base import BaseCommand
from kombu import Exchange, Queue

from awx.main.dispatch import get_local_queuename
from awx.main.dispatch.control import Control
from awx.main.dispatch.kombu import Connection
from awx.main.dispatch.worker import AWXConsumer, CallbackBrokerWorker


class Command(BaseCommand):
    '''
    Save Job Callback receiver
    Runs as a management command and receives job save events.  It then hands
    them off to worker processors (see Worker) which writes them to the database
    '''
    help = 'Launch the job callback receiver'

    def add_arguments(self, parser):
        parser.add_argument('--status', dest='status', action='store_true',
                            help='print the internal state of any running callback receiver')

    def handle(self, *arg, **options):
        control_routing_key = 'callback_receiver-{}-control'.format(get_local_queuename())
        if options.get('status'):
            print(Control(
                'callback_receiver',
                host=settings.CALLBACK_QUEUE,
                routing_key=control_routing_key
            ).status())
            return

        with Connection(settings.BROKER_URL) as conn:
            consumer = None
            try:
                queues = [
                    Queue(
                        settings.CALLBACK_QUEUE,
                        Exchange(settings.CALLBACK_QUEUE, type='direct'),
                        routing_key=settings.CALLBACK_QUEUE
                    ),
                    Queue(
                        settings.CALLBACK_QUEUE,
                        Exchange(settings.CALLBACK_QUEUE, type='direct'),
                        routing_key=control_routing_key,
                    )
                ]
                consumer = AWXConsumer(
                    'callback_receiver',
                    conn,
                    CallbackBrokerWorker(),
                    queues
                )
                consumer.run()
            except KeyboardInterrupt:
                print('Terminating Callback Receiver')
                if consumer:
                    consumer.stop()
