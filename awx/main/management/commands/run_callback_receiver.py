# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from redis.exceptions import ConnectionError

from awx.main.analytics.subsystem_metrics import CallbackReceiverMetricsServer
from awx.main.dispatch.control import Control
from awx.main.dispatch.worker import AWXConsumerRedis, CallbackBrokerWorker


class Command(BaseCommand):
    """
    Save Job Callback receiver
    Runs as a management command and receives job save events.  It then hands
    them off to worker processors (see Worker) which writes them to the database
    """

    help = 'Launch the job callback receiver'

    def add_arguments(self, parser):
        parser.add_argument('--status', dest='status', action='store_true', help='print the internal state of any running dispatchers')

    def handle(self, *arg, **options):
        if options.get('status'):
            print(Control('callback_receiver').status())
            return
        consumer = None

        try:
            CallbackReceiverMetricsServer().start()
        except ConnectionError as exc:
            raise CommandError(f'Could not connect to redis, error:\n{exc}\n')

        try:
            consumer = AWXConsumerRedis(
                'callback_receiver',
                CallbackBrokerWorker(),
                queues=[getattr(settings, 'CALLBACK_QUEUE', '')],
            )
            consumer.run()
        except KeyboardInterrupt:
            print('Terminating Callback Receiver')
            if consumer:
                consumer.stop()
