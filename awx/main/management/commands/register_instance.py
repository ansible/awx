# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from awx.main.models import Instance
from django.conf import settings

from optparse import make_option
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    """
    Internal tower command.
    Regsiter this instance with the database for HA tracking.
    """

    option_list = BaseCommand.option_list + (
        make_option('--hostname', dest='hostname', type='string',
                    help='Hostname used during provisioning'),
    )

    def handle(self, **options):
        uuid = settings.SYSTEM_UUID
        instance = Instance.objects.filter(hostname=options.get('hostname'))
        if instance.exists():
            print("Instance already registered {}".format(instance[0]))
            return
        instance = Instance(uuid=uuid, hostname=options.get('hostname'))
        instance.save()
        print('Successfully registered instance {}'.format(instance))
