# Copyright (c) 2016 Ansible, Inc.
# All Rights Reserved
import redis
from django.db import transaction
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from awx.main.models import Instance
from awx.main.utils.pglock import advisory_lock
from awx.main.analytics.subsystem_metrics import root_key


class Command(BaseCommand):
    """
    Deprovision a cluster node
    """

    help = 'Remove instance from the database. ' 'Specify `--hostname` to use this command.'

    def add_arguments(self, parser):
        parser.add_argument('--hostname', dest='hostname', type=str, help='Hostname used during provisioning')

    @transaction.atomic
    def handle(self, *args, **options):
        # TODO: remove in 3.3
        hostname = options.get('hostname')
        if not hostname:
            raise CommandError("--hostname is a required argument")
        # remove redis metrics keys
        conn = redis.Redis.from_url(settings.BROKER_URL)
        metrics_key = root_key + '_instance_' + hostname
        if conn.exists(metrics_key):
            conn.delete(metrics_key)
            print(f"Removed {hostname} metric data from redis")

        with advisory_lock('instance_registration_%s' % hostname):
            instance = Instance.objects.filter(hostname=hostname)
            if instance.exists():
                instance.delete()
                print("Instance Removed")
                print('Successfully deprovisioned {}'.format(hostname))
                print('(changed: True)')
            else:
                print('No instance found matching name {}'.format(hostname))
