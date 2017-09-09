# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved

from optparse import make_option
import subprocess
import warnings

from django.db import transaction
from django.core.management.base import BaseCommand, CommandError

from awx.main.models import Instance
from awx.main.utils.pglock import advisory_lock


class Command(BaseCommand):
    """
    Deprovision a Tower cluster node
    """

    help = (
        'Remove instance from the database. '
        'Specify `--hostname` to use this command.'
    )

    option_list = BaseCommand.option_list + (
        make_option('--hostname', dest='hostname', type='string',
                    help='Hostname used during provisioning'),
        make_option('--name', dest='name', type='string',
                    help='(PENDING DEPRECIATION) Hostname used during provisioning'),
    )

    @transaction.atomic
    def handle(self, *args, **options):
        # TODO: remove in 3.3
        if options.get('name'):
            warnings.warn("`--name` is depreciated in favor of `--hostname`, and will be removed in release 3.3.")
            if options.get('hostname'):
                raise CommandError("Cannot accept both --name and --hostname.")
            options['hostname'] = options['name']
        hostname = options.get('hostname')
        if not hostname:
            raise CommandError("--hostname is a required argument")
        with advisory_lock('instance_registration_%s' % hostname):
            instance = Instance.objects.filter(hostname=hostname)
            if instance.exists():
                instance.delete()
                print("Instance Removed")
                result = subprocess.Popen("rabbitmqctl forget_cluster_node rabbitmq@{}".format(hostname), shell=True).wait()
                if result != 0:
                    print("Node deprovisioning may have failed when attempting to "
                          "remove the RabbitMQ instance {} from the cluster".format(hostname))
                else:
                    print('Successfully deprovisioned {}'.format(hostname))
                print('(changed: True)')
            else:
                print('No instance found matching name {}'.format(hostname))

