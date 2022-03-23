# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand
from django.db import transaction

from awx.main.models import Instance


class Command(BaseCommand):
    """
    Internal tower command.
    Register this instance with the database for HA tracking.
    """

    help = "Add instance to the database. Specify `--hostname` to use this command."

    def add_arguments(self, parser):
        parser.add_argument('--hostname', dest='hostname', type=str, help="Hostname used during provisioning")
        parser.add_argument('--node_type', type=str, default='hybrid', choices=['control', 'execution', 'hop', 'hybrid'], help="Instance Node type")
        parser.add_argument('--uuid', type=str, help="Instance UUID")

    def _register_hostname(self, hostname, node_type, uuid):
        if not hostname:
            (changed, instance) = Instance.objects.get_or_register()
        else:
            (changed, instance) = Instance.objects.register(hostname=hostname, node_type=node_type, uuid=uuid)
        if changed:
            print("Successfully registered instance {}".format(hostname))
        else:
            print("Instance already registered {}".format(instance.hostname))
        self.changed = changed

    @transaction.atomic
    def handle(self, **options):
        self.changed = False
        self._register_hostname(options.get('hostname'), options.get('node_type'), options.get('uuid'))
        if self.changed:
            print("(changed: True)")
