# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from ansible_base.lib.utils.db import advisory_lock

from awx.main.models import Instance


class Command(BaseCommand):
    """
    Deprovision a cluster node
    """

    help = 'Remove instance from the database. Specify `--hostname` to use this command.'

    def add_arguments(self, parser):
        parser.add_argument('--hostname', dest='hostname', type=str, help='Hostname used during provisioning')

    @transaction.atomic
    def handle(self, *args, **options):
        # TODO: remove in 3.3
        hostname = options.get('hostname')
        if hostname is None:
            raise CommandError("--hostname is a required argument")
        # Installers may pass an empty --hostname= when Instance.hostname is blank
        # or gather stdout includes an empty line (AAP-75757). Skip instead of failing.
        hostname = hostname.strip()
        if not hostname:
            print('Skipping deprovision of empty hostname')
            print('(changed: False)')
            return
        with advisory_lock('instance_registration_%s' % hostname):
            instance = Instance.objects.filter(hostname=hostname)
            if instance.exists():
                instance.delete()
                print("Instance Removed")
                print('Successfully deprovisioned {}'.format(hostname))
                print('(changed: True)')
            else:
                print('No instance found matching name {}'.format(hostname))
