# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from awx.main.models import Instance
from awx.main.utils.pglock import advisory_lock
from django.conf import settings

from optparse import make_option
from django.db import transaction
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """
    Internal tower command.
    Regsiter this instance with the database for HA tracking.
    """

    option_list = BaseCommand.option_list + (
        make_option('--hostname', dest='hostname', type='string',
                    help='Hostname used during provisioning'),
        make_option('--hostnames', dest='hostnames', type='string',
                    help='Alternatively hostnames can be provided with '
                         'this option as a comma-Delimited list'),
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
        self.uuid = settings.SYSTEM_UUID
        self.changed = False
        self._register_hostname(options.get('hostname'))
        hostname_list = []
        if options.get('hostnames'):
            hostname_list = options.get('hostnames').split(",")
        instance_list = [x.strip() for x in hostname_list if x]
        for inst_name in instance_list:
            self._register_hostname(inst_name)
        if self.changed:
            print('(changed: True)')
