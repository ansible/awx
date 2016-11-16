# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

# Python
import logging

# Django
from django.db import transaction
from django.core.management.base import BaseCommand
from django.utils.timezone import now

# AWX
from awx.main.models import * # noqa


class Command(BaseCommand):
    '''
    Management command to cleanup expired auth tokens
    '''

    help = 'Cleanup expired auth tokens.'

    def init_logging(self):
        self.logger = logging.getLogger('awx.main.commands.cleanup_authtokens')
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    @transaction.atomic
    def handle(self, *args, **options):
        self.init_logging()
        tokens_removed = AuthToken.objects.filter(expires__lt=now())
        self.logger.log(99, "Removing %d expired auth tokens" % tokens_removed.count())
        tokens_removed.delete()
