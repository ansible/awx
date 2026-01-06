# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import logging
import logging.config
import yaml
import copy

import redis

from django.conf import settings
from django.db import connection
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache as django_cache

from flags.state import flag_enabled

from dispatcherd.factories import get_control_from_settings
from dispatcherd import run_service
from dispatcherd.config import setup as dispatcher_setup

from awx.main.dispatch import get_task_queuename
from awx.main.dispatch.config import get_dispatcherd_config
from awx.main.dispatch.control import Control
from awx.main.dispatch.pool import AutoscalePool
from awx.main.dispatch.worker import AWXConsumerPG, TaskWorker
from awx.main.analytics.subsystem_metrics import DispatcherMetricsServer

logger = logging.getLogger('awx.main.dispatch')


class Command(BaseCommand):
    help = 'Launch the task dispatcher'

    def add_arguments(self, parser):
        parser.add_argument('--status', dest='status', action='store_true', help='print the internal state of any running dispatchers')
        parser.add_argument('--schedule', dest='schedule', action='store_true', help='print the current status of schedules being ran by dispatcher')
        parser.add_argument('--running', dest='running', action='store_true', help='print the UUIDs of any tasked managed by this dispatcher')
        parser.add_argument(
            '--reload',
            dest='reload',
            action='store_true',
            help=('cause the dispatcher to recycle all of its worker processes; running jobs will run to completion first'),
        )
        parser.add_argument(
            '--cancel',
            dest='cancel',
            help=(
                'Cancel a particular task id. Takes either a single id string, or a JSON list of multiple ids. '
                'Can take in output from the --running argument as input to cancel all tasks. '
                'Only running tasks can be canceled, queued tasks must be started before they can be canceled.'
            ),
        )

    def handle(self, *arg, **options):
        if options.get('status'):
            if flag_enabled('FEATURE_DISPATCHERD_ENABLED'):
                ctl = get_control_from_settings()
                running_data = ctl.control_with_reply('status')
                if len(running_data) != 1:
                    raise CommandError('Did not receive expected number of replies')
                print(yaml.dump(running_data[0], default_flow_style=False))
                return
            else:
                print(Control('dispatcher').status())
                return
        if options.get('schedule'):
            if flag_enabled('FEATURE_DISPATCHERD_ENABLED'):
                print('NOT YET IMPLEMENTED')
                return
            else:
                print(Control('dispatcher').schedule())
            return
        if options.get('running'):
            if flag_enabled('FEATURE_DISPATCHERD_ENABLED'):
                ctl = get_control_from_settings()
                running_data = ctl.control_with_reply('running')
                print(yaml.dump(running_data, default_flow_style=False))
                return
            else:
                print(Control('dispatcher').running())
                return
        if options.get('reload'):
            if flag_enabled('FEATURE_DISPATCHERD_ENABLED'):
                print('NOT YET IMPLEMENTED')
                return
            else:
                return Control('dispatcher').control({'control': 'reload'})
        if options.get('cancel'):
            cancel_str = options.get('cancel')
            try:
                cancel_data = yaml.safe_load(cancel_str)
            except Exception:
                cancel_data = [cancel_str]
            if not isinstance(cancel_data, list):
                cancel_data = [cancel_str]

            if flag_enabled('FEATURE_DISPATCHERD_ENABLED'):
                ctl = get_control_from_settings()
                results = []
                for task_id in cancel_data:
                    # For each task UUID, send an individual cancel command
                    result = ctl.control_with_reply('cancel', data={'uuid': task_id})
                    results.append(result)
                print(yaml.dump(results, default_flow_style=False))
                return
            else:
                print(Control('dispatcher').cancel(cancel_data))
                return

        if flag_enabled('FEATURE_DISPATCHERD_ENABLED'):
            self.configure_dispatcher_logging()

            # Close the connection, because the pg_notify broker will create new async connection
            connection.close()
            django_cache.close()

            dispatcher_setup(get_dispatcherd_config(for_service=True))
            run_service()
        else:
            consumer = None

            try:
                DispatcherMetricsServer().start()
            except redis.exceptions.ConnectionError as exc:
                raise CommandError(f'Dispatcher could not connect to redis, error: {exc}')

            try:
                queues = ['tower_broadcast_all', 'tower_settings_change', get_task_queuename()]
                consumer = AWXConsumerPG('dispatcher', TaskWorker(), queues, AutoscalePool(min_workers=4), schedule=settings.CELERYBEAT_SCHEDULE)
                consumer.run()
            except KeyboardInterrupt:
                logger.debug('Terminating Task Dispatcher')
                if consumer:
                    consumer.stop()

    def configure_dispatcher_logging(self):
        # Apply special log rule for the parent process
        special_logging = copy.deepcopy(settings.LOGGING)
        for handler_name, handler_config in special_logging.get('handlers', {}).items():
            filters = handler_config.get('filters', [])
            if 'dynamic_level_filter' in filters:
                handler_config['filters'] = [flt for flt in filters if flt != 'dynamic_level_filter']
                logger.info(f'Dispatcherd main process replaced log level filter for {handler_name} handler')

        # Apply the custom logging level here, before the asyncio code starts
        special_logging.setdefault('loggers', {}).setdefault('dispatcherd', {})
        special_logging['loggers']['dispatcherd']['level'] = settings.LOG_AGGREGATOR_LEVEL

        logging.config.dictConfig(special_logging)
