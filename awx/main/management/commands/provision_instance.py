# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings

from awx.main.models import Instance


class Command(BaseCommand):
    """
    Internal tower command.
    Register this instance with the database for HA tracking.
    """

    help = (
        "Add instance to the database. "
        "When no options are provided, values from Django settings will be used to register the current system, "
        "as well as the default queues if needed (only used or enabled for Kubernetes installs). "
        "Override with `--hostname`."
    )

    def add_arguments(self, parser):
        parser.add_argument('--hostname', dest='hostname', type=str, help="Hostname used during provisioning")
        parser.add_argument('--node_type', type=str, default='hybrid', choices=['control', 'execution', 'hop', 'hybrid'], help="Instance Node type")
        parser.add_argument('--uuid', type=str, help="Instance UUID")

    def _register_hostname(self, hostname, node_type, uuid):
        if not hostname:
            if not settings.AWX_AUTO_DEPROVISION_INSTANCES:
                raise CommandError('Registering with values from settings only intended for use in K8s installs')

            from awx.main.management.commands.register_queue import RegisterQueue

            (changed, instance) = Instance.objects.register(ip_address=os.environ.get('MY_POD_IP'), node_type='control', node_uuid=settings.SYSTEM_UUID)
            RegisterQueue(settings.DEFAULT_CONTROL_PLANE_QUEUE_NAME, 100, 0, [], is_container_group=False).register()
            RegisterQueue(
                settings.DEFAULT_EXECUTION_QUEUE_NAME,
                100,
                0,
                [],
                is_container_group=True,
                pod_spec_override=settings.DEFAULT_EXECUTION_QUEUE_POD_SPEC_OVERRIDE,
                max_forks=settings.DEFAULT_EXECUTION_QUEUE_MAX_FORKS,
                max_concurrent_jobs=settings.DEFAULT_EXECUTION_QUEUE_MAX_CONCURRENT_JOBS,
            ).register()
        else:
            (changed, instance) = Instance.objects.register(hostname=hostname, node_type=node_type, node_uuid=uuid)
        if changed:
            print("Successfully registered instance {}".format(hostname))
        else:
            print("Instance already registered {}".format(instance.hostname))
        self.changed = changed

    @transaction.atomic
    def handle(self, **options):
        self.changed = False
        self._register_hostname(options.get('hostname'), options.get('node_type'), options.get('uuid'))
        if self.changed:
            print("(changed: True)")
