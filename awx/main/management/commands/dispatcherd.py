# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved
import copy
import hashlib
import json
import logging
import logging.config
import os

from django.conf import settings
from django.core.cache import cache as django_cache
from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from dispatcherd.config import setup as dispatcher_setup

from awx.main.dispatch.config import get_dispatcherd_config

logger = logging.getLogger('awx.main.dispatch')


from dispatcherd import run_service


def _json_default(value):
    if isinstance(value, set):
        return sorted(value)
    if isinstance(value, tuple):
        return list(value)
    return str(value)


def _hash_config(config):
    serialized = json.dumps(config, sort_keys=True, separators=(',', ':'), default=_json_default)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()


def ensure_no_dispatcherd_env_config():
    if os.getenv('DISPATCHERD_CONFIG_FILE'):
        raise CommandError('DISPATCHERD_CONFIG_FILE is set but awx-manage dispatcherd uses dynamic config from code')


class Command(BaseCommand):
    help = (
        'Run the background task service, this is the supported entrypoint since the introduction of dispatcherd as a library. '
        'This replaces the prior awx-manage run_dispatcher service, and control actions are at awx-manage dispatcherctl.'
    )

    def add_arguments(self, parser):
        return

    def handle(self, *arg, **options):
        ensure_no_dispatcherd_env_config()

        self.configure_dispatcher_logging()
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

        run_service()

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
