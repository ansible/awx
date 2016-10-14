# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved

from django.core.management.base import BaseCommand
from optparse import make_option
from awx.main.models import Instance


class Command(BaseCommand):
    """
    Deprovision a Tower cluster node
    """

    option_list = BaseCommand.option_list + (
        make_option('--name', dest='name', type='string',
                    help='Hostname used during provisioning'),
    )

    def handle(self, **options):
        # Get the instance.
        instance = Instance.objects.filter(hostname=options.get('name'))
        if instance.exists():
            instance.delete()
            print('Successfully removed')
        else:
            print('No instance found matching name {}'.format(options.get('name')))

