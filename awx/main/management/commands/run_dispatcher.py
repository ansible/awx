# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.
import logging

from awx.main.management.commands.dispatcherd import Command as DispatcherdCommand

logger = logging.getLogger('awx.main.dispatch')


class Command(DispatcherdCommand):
    help = 'Launch the task dispatcher (deprecated; use awx-manage dispatcherd)'

    def handle(self, *args, **options):
        logger.warning('awx-manage run_dispatcher is deprecated; use awx-manage dispatcherd')
        return super().handle(*args, **options)
