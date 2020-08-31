# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from uuid import uuid4

from awx.main.models import Instance
from django.conf import settings

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """
    Internal tower command.
    Register this instance with the database for HA tracking.
    """

    help = (
        'Add instance to the database. '
        'Specify `--hostname` to use this command.'
    )

    def add_arguments(self, parser):
        parser.add_argument('--hostname', dest='hostname', type=str,
                            help='Hostname used during provisioning')
        parser.add_argument('--is-isolated', dest='is_isolated', action='store_true',
                            help='Specify whether the instance is isolated')

    def _register_hostname(self, hostname):
        if not hostname:
            return
        (changed, instance) = Instance.objects.register(uuid=self.uuid, hostname=hostname)
        if changed:
            print('Successfully registered instance {}'.format(hostname))
        else:
            print("Instance already registered {}".format(instance.hostname))
        self.changed = changed

    @transaction.atomic
    def handle(self, **options):
        if not options.get('hostname'):
            raise CommandError("Specify `--hostname` to use this command.")
        if options['is_isolated']:
            self.uuid = str(uuid4())
        else:
            self.uuid = settings.SYSTEM_UUID
        self.changed = False
        self._register_hostname(options.get('hostname'))
        if self.changed:
            print('(changed: True)')
