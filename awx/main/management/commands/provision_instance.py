# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from awx.main.models import Instance
from awx.main.utils.pglock import advisory_lock
from django.conf import settings

from optparse import make_option
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    """
    Internal tower command.
    Regsiter this instance with the database for HA tracking.
    """

    help = (
        'Add instance to the database. '
        'Specify `--hostname` to use this command.'
    )

    option_list = BaseCommand.option_list + (
        make_option('--hostname', dest='hostname', type='string',
                    help='Hostname used during provisioning'),
    )

    def _register_hostname(self, hostname):
        if not hostname:
            return
        with advisory_lock('instance_registration_%s' % hostname):
            instance = Instance.objects.filter(hostname=hostname)
            if instance.exists():
                print("Instance already registered {}".format(instance[0].hostname))
                return
            instance = Instance(uuid=self.uuid, hostname=hostname)
            instance.save()
        print('Successfully registered instance {}'.format(hostname))
        self.changed = True

    @transaction.atomic
    def handle(self, **options):
        if not options.get('hostname'):
            raise CommandError("Specify `--hostname` to use this command.")
        self.uuid = settings.SYSTEM_UUID
        self.changed = False
        self._register_hostname(options.get('hostname'))
        if self.changed:
            print('(changed: True)')
