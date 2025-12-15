import argparse
import inspect
import logging
import os
import sys

import yaml

from django.core.management.base import BaseCommand, CommandError

from dispatcherd.cli import (
    CONTROL_ARG_SCHEMAS,
    DEFAULT_CONFIG_FILE,
    _base_cli_parent,
    _control_common_parent,
    _register_control_arguments,
    _build_command_data_from_args,
)
from dispatcherd.config import setup as dispatcher_setup
from dispatcherd.factories import get_control_from_settings
from dispatcherd.service import control_tasks

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Dispatcher control operations'

    def add_arguments(self, parser):
        parser.description = 'Run dispatcherd control commands using awx-manage.'
        base_parent = _base_cli_parent()
        control_parent = _control_common_parent()
        parser._add_container_actions(base_parent)
        parser._add_container_actions(control_parent)

        subparsers = parser.add_subparsers(dest='command', metavar='command')
        subparsers.required = True
        shared_parents = [base_parent, control_parent]
        for command in control_tasks.__all__:
            func = getattr(control_tasks, command, None)
            doc = inspect.getdoc(func) or ''
            summary = doc.splitlines()[0] if doc else None
            command_parser = subparsers.add_parser(
                command,
                help=summary,
                description=doc,
                parents=shared_parents,
            )
            _register_control_arguments(command_parser, CONTROL_ARG_SCHEMAS.get(command))

    def handle(self, *args, **options):
        command = options.get('command')
        if not command:
            raise CommandError('No dispatcher control command specified')

        for django_opt in ('verbosity', 'traceback', 'no_color', 'force_color', 'skip_checks'):
            options.pop(django_opt, None)

        log_level = options.pop('log_level', 'DEBUG')
        config_path = os.path.abspath(options.pop('config', DEFAULT_CONFIG_FILE))
        expected_replies = options.pop('expected_replies', 1)

        logging.basicConfig(level=getattr(logging, log_level), stream=sys.stdout)
        logger.debug(f"Configured standard out logging at {log_level} level")

        env_config = os.getenv('DISPATCHERD_CONFIG_FILE')
        default_config = os.path.abspath(DEFAULT_CONFIG_FILE)
        if env_config and config_path == default_config:
            logger.info(f'Using config from environment variable DISPATCHERD_CONFIG_FILE={env_config}')
            dispatcher_setup()
        else:
            logger.info(f'Using config from file {config_path}')
            dispatcher_setup(file_path=config_path)

        schema_namespace = argparse.Namespace(**options)
        data = _build_command_data_from_args(schema_namespace, command)

        ctl = get_control_from_settings()
        returned = ctl.control_with_reply(command, data=data, expected_replies=expected_replies)
        self.stdout.write(yaml.dump(returned, default_flow_style=False))
        if len(returned) < expected_replies:
            logger.error(f'Obtained only {len(returned)} of {expected_replies}, exiting with non-zero code')
            raise CommandError('dispatcherctl returned fewer replies than expected')
