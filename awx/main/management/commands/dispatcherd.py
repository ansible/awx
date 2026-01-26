# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved
import copy
import hashlib
import json
import logging
import logging.config
import os

import yaml

from django.conf import settings
from django.core.cache import cache as django_cache
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dispatcherd.config import setup as dispatcher_setup
from dispatcherd.factories import get_control_from_settings

from awx.main.dispatch.config import get_dispatcherd_config

logger = logging.getLogger('awx.main.dispatch')


def _dispatcherd_entrypoint():
    try:
        from dispatcherd import cli as dispatcherd_cli
    except Exception:
        from dispatcherd import run_service

        return run_service

    for name in ('dispatcherd_main', 'main'):
        entrypoint = getattr(dispatcherd_cli, name, None)
        if callable(entrypoint):
            return entrypoint

    try:
        import dispatcherd.__main__ as dispatcherd_main_module
    except Exception:
        dispatcherd_main_module = None

    if dispatcherd_main_module is not None:
        entrypoint = getattr(dispatcherd_main_module, 'main', None)
        if callable(entrypoint):
            return entrypoint

    from dispatcherd import run_service

    return run_service


def _json_default(value):
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, tuple):
        return list(value)
    return str(value)


def _hash_config(config):
    serialized = json.dumps(config, sort_keys=True, separators=(',', ':'), default=_json_default)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


class Command(BaseCommand):
    help = 'Launch the task dispatcher'

    def add_arguments(self, parser):
        parser.add_argument('--status', dest='status', action='store_true', help='print the internal state of any running dispatchers')
        parser.add_argument('--running', dest='running', action='store_true', help='print the UUIDs of any tasked managed by this dispatcher')
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
            ctl = get_control_from_settings()
            running_data = ctl.control_with_reply('status')
            if len(running_data) != 1:
                raise CommandError('Did not receive expected number of replies')
            print(yaml.dump(running_data[0], default_flow_style=False))
            return
        if options.get('running'):
            ctl = get_control_from_settings()
            running_data = ctl.control_with_reply('running')
            print(yaml.dump(running_data, default_flow_style=False))
            return
        if options.get('cancel'):
            cancel_str = options.get('cancel')
            try:
                cancel_data = yaml.safe_load(cancel_str)
            except Exception:
                cancel_data = [cancel_str]
            if not isinstance(cancel_data, list):
                cancel_data = [cancel_str]

            ctl = get_control_from_settings()
            results = []
            for task_id in cancel_data:
                # For each task UUID, send an individual cancel command
                result = ctl.control_with_reply('cancel', data={'uuid': task_id})
                results.append(result)
            print(yaml.dump(results, default_flow_style=False))
            return

        self.configure_dispatcher_logging()
        if os.getenv('DISPATCHERD_CONFIG_FILE'):
            raise CommandError('DISPATCHERD_CONFIG_FILE is set but awx-manage dispatcherd uses dynamic config from code')

        config = get_dispatcherd_config(for_service=True)
        config_hash = _hash_config(config)
        logger.info(
            'Using dispatcherd config generated from awx.main.dispatch.config.get_dispatcherd_config (sha256=%s)',
            config_hash,
        )

        # Close the connection, because the pg_notify broker will create new async connection
        connection.close()
        django_cache.close()
        dispatcher_setup(config)

        _dispatcherd_entrypoint()()

    def configure_dispatcher_logging(self):
        # Apply special log rule for the parent process
        special_logging = copy.deepcopy(settings.LOGGING)
        changed_handlers = []
        for handler_name, handler_config in special_logging.get('handlers', {}).items():
            filters = handler_config.get('filters', [])
            if 'dynamic_level_filter' in filters:
                handler_config['filters'] = [flt for flt in filters if flt != 'dynamic_level_filter']
                changed_handlers.append(handler_name)
        logger.info(f'Dispatcherd main process replaced log level filter for handlers: {changed_handlers}')

        # Apply the custom logging level here, before the asyncio code starts
        special_logging.setdefault('loggers', {}).setdefault('dispatcherd', {})
        special_logging['loggers']['dispatcherd']['level'] = settings.LOG_AGGREGATOR_LEVEL

        logging.config.dictConfig(special_logging)
