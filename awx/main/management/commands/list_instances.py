# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved

from awx.main.models import Instance, InstanceGroup
from django.core.management.base import BaseCommand


class Ungrouped(object):

    name = 'ungrouped'
    policy_instance_percentage = None
    policy_instance_minimum = None
    controller = None

    @property
    def instances(self):
        return Instance.objects.filter(rampart_groups__isnull=True)

    @property
    def capacity(self):
        return sum([x.capacity for x in self.instances])


class Command(BaseCommand):
    """List instances from the Tower database
    """

    def handle(self, *args, **options):
        super(Command, self).__init__()

        groups = list(InstanceGroup.objects.all())
        ungrouped = Ungrouped()
        if len(ungrouped.instances):
            groups.append(ungrouped)

        for instance_group in groups:
            fmt = '[{0.name} capacity={0.capacity}'
            if instance_group.policy_instance_percentage:
                fmt += ' policy={0.policy_instance_percentage}%'
            if instance_group.policy_instance_minimum:
                fmt += ' policy>={0.policy_instance_minimum}'
            if instance_group.controller:
                fmt += ' controller={0.controller.name}'
            print((fmt + ']').format(instance_group))
            for x in instance_group.instances.all():
                color = '\033[92m'
                if x.capacity == 0:
                    color = '\033[91m'
                if x.enabled is False:
                    color = '\033[90m[DISABLED] '
                fmt = '\t' + color + '{0.hostname} capacity={0.capacity} version={1}'
                if x.last_isolated_check:
                    fmt += ' last_isolated_check="{0.last_isolated_check:%Y-%m-%d %H:%M:%S}"'
                if x.capacity:
                    fmt += ' heartbeat="{0.modified:%Y-%m-%d %H:%M:%S}"'
                print((fmt + '\033[0m').format(x, x.version or '?'))
            print('')
