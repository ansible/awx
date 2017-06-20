# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved

import subprocess
from django.core.management.base import BaseCommand, CommandError
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

    def handle(self, *args, **options):
        if not options.get('name'):
            raise CommandError("--name is a required argument")
        instance = Instance.objects.filter(hostname=options.get('name'))
        if instance.exists():
            instance.delete()
            print("Instance Removed")
            result = subprocess.Popen("rabbitmqctl forget_cluster_node rabbitmq@{}".format(options.get('name')), shell=True).wait()
            if result != 0:
                print("Node deprovisioning may have failed when attempting to remove the RabbitMQ instance from the cluster")
            else:
                print('Successfully deprovisioned {}'.format(options.get('name')))
            print('(changed: True)')
        else:
            print('No instance found matching name {}'.format(options.get('name')))

