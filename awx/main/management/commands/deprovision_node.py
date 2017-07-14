# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved

from optparse import make_option
import subprocess

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from awx.main.models import Instance
from awx.main.utils.pglock import advisory_lock


class Command(BaseCommand):
    """
    Deprovision a Tower cluster node
    """

    option_list = BaseCommand.option_list + (
        make_option('--name', dest='name', type='string',
                    help='Hostname used during provisioning'),
    )

    @transaction.atomic
    def handle(self, *args, **options):
        hostname = options.get('name')
        if not hostname:
            raise CommandError("--name is a required argument")
        with advisory_lock('instance_registration_%s' % hostname):
            instance = Instance.objects.filter(hostname=hostname)
            if instance.exists():
                instance.delete()
                print("Instance Removed")
                result = subprocess.Popen("rabbitmqctl forget_cluster_node rabbitmq@{}".format(hostname), shell=True).wait()
                if result != 0:
                    print("Node deprovisioning may have failed when attempting to remove the RabbitMQ instance from the cluster")
                else:
                    print('Successfully deprovisioned {}'.format(hostname))
                print('(changed: True)')
            else:
                print('No instance found matching name {}'.format(hostname))

