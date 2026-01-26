# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import logging

import yaml

from django.core.management.base import CommandError

from dispatcherd.factories import get_control_from_settings

from awx.main.management.commands.dispatcherd import Command as DispatcherdCommand

logger = logging.getLogger('awx.main.dispatch')


class Command(DispatcherdCommand):
    help = 'Launch the task dispatcher (deprecated; use awx-manage dispatcherd)'

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
        super().add_arguments(parser)

    def handle(self, *args, **options):
        logger.warning('awx-manage run_dispatcher is deprecated; use awx-manage dispatcherd')
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
        return super().handle(*args, **options)
