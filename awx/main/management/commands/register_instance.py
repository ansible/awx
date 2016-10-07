# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from awx.main.models import Instance
from django.conf import settings

from django.core.management.base import CommandError, NoArgsCommand

class Command(NoArgsCommand):
    """
    Internal tower command.
    Regsiter this instance with the database for HA tracking.
    """

    option_list = NoArgsCommand.option_list + (
        make_option('--hostname', dest='hostname', type='string',
                    help='Hostname used during provisioning')
    )

    def handle(self, *args, **options):
        super(Command, self).handle(**options)
        uuid = settings.SYSTEM_UUID

        instance = Instance.objects.filter(hostname=options.get('hostname'))
        if instance.exists():
            print("Instance already registered %s" % instance_str(instance[0]))
            return
        instance = Instance(uuid=uuid, hostname=options.get('hostname'))
        instance.save()
        print('Successfully registered instance %s.' % instance_str(instance))
